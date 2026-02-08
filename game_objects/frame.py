from functools import cached_property

import cv2
import numpy as np

from cv_tools.strip_frame import strip_frame
from cv_tools.debug import save_image
from cv_tools.detect_digit import detect_digit, get_refs, RoiRef
from cv_tools.find_game_over import find_game_over
from cv_tools.score_detect import get_countours

Point = tuple[int, int]
Rect = tuple[Point, Point]


class BaseFrame:
    def __init__(self, image: np.array):
        self.image = image

    def crop(self, rect: Rect):
        return self.image[rect[0][0] : rect[1][0], rect[0][1] : rect[1][1]]

    @staticmethod
    def crop_image(image: np.array, rect: Rect):
        return image[rect[0][0] : rect[1][0], rect[0][1] : rect[1][1]]

    def mask(self, lower=(10, 10, 10), upper=(255, 255, 255)):
        mask = cv2.inRange(self.image, lower, upper)
        return mask


class SideScoreFrame(BaseFrame):
    def __init__(self, image: np.array, roi_ref: RoiRef):
        super().__init__(image)
        self.roi_ref = roi_ref

    def mid_line(self, image: np.array):
        raise NotImplementedError()

    def strip(self, image: np.array) -> int:
        raise NotImplementedError()

    @cached_property
    def lines_pos(self) -> tuple[Rect, Rect, Rect]:
        """Find three horizontal regions for score, lines, and level.

        Divides the image into three roughly equal parts, ensuring each
        region is tall enough to contain digit templates (~40 pixels).
        """
        height = self.image.shape[0]
        width = self.image.shape[1]

        # Divide into three regions with some overlap to ensure digits are captured
        # Each region should be at least 50 pixels tall for reliable digit detection
        third = height // 3
        min_height = 50

        # Score region: top third
        score_end = max(third, min_height)

        # Lines region: middle third (with some overlap)
        lines_start = third - 10 if third > 10 else 0
        lines_end = 2 * third + 10

        # Level region: bottom third
        level_start = 2 * third - 10 if 2 * third > 10 else third

        return (
            ((0, 0), (score_end, width)),
            ((lines_start, 0), (lines_end, width)),
            ((level_start, 0), (height, width)),
        )

    @property
    def lines_stripped(self) -> tuple[Rect, Rect, Rect]:
        raise NotImplementedError()

    @cached_property
    def is_next(self) -> bool:
        img = self.mask(lower=(0, 0, 150), upper=(100, 100, 255))
        # save_image("next.png", img)
        return cv2.countNonZero(img) > 100

    def get_line(self, n: int) -> int | None:
        if not self.is_next:
            return

        i = self.lines_stripped[n]

        img = self.crop_image(self.image, i)

        im_bw = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        _, thresh_original = cv2.threshold(im_bw, 50, 255, cv2.THRESH_BINARY)

        countours = get_countours(thresh_original)
        # for n, i in enumerate(countours):
        #     save_image("countour_{}.png".format(n), i)

        digits = [detect_digit(i, self.roi_ref) for i in countours]
        # Filter out empty results from invalid contours
        digits = [d for d in digits if d]

        if not digits:
            return None
        return int("".join(digits))

    @cached_property
    def score(self):
        return self.get_line(0)

    @cached_property
    def lines(self):
        return self.get_line(1)

    @cached_property
    def level(self):
        return self.get_line(2)


class LeftScoreFrame(SideScoreFrame):
    def mid_line(self, image: np.array):
        return image[:, -1:]

    @cached_property
    def lines_stripped(self) -> list[Rect]:
        mask = self.mask()

        def strip(image: np.array) -> int:
            """Find where score digits start - scan from right to find content."""
            if image.shape[0] == 0 or image.shape[1] == 0:
                return 0
            # Use vertical projection - scan from right to find where content starts
            col_sums = np.sum(image, axis=0)
            # Find rightmost non-zero column (end of content)
            end = None
            for i in range(len(col_sums) - 1, -1, -1):
                if col_sums[i] > 0:
                    end = i + 1
                    break
            if end is None:
                return 0
            # Find a significant gap (5+ zeros) before content, scanning from right
            consecutive_zeros = 0
            min_gap = 5
            for i in range(end - 1, -1, -1):
                if col_sums[i] == 0:
                    consecutive_zeros += 1
                    if consecutive_zeros >= min_gap:
                        return i + min_gap
                else:
                    consecutive_zeros = 0
            return 0

        lines = self.lines_pos
        offsets = [strip(self.crop_image(mask, i)) for i in lines]

        stripped = [
            ((line[0][0], s), (line[1][0], line[1][1]))
            for line, s in zip(lines, offsets)
        ]

        return stripped


class RightScoreFrame(SideScoreFrame):
    def mid_line(self, image: np.array):
        return image[:, :1]

    @cached_property
    def lines_stripped(self) -> list[Rect]:
        mask = self.mask()

        def strip(image: np.array) -> int:
            """Find where score digits end using vertical projection."""
            if image.shape[0] == 0 or image.shape[1] == 0:
                return None
            # Sum columns vertically - columns with digits will have high sums
            col_sums = np.sum(image, axis=0)
            # Find first non-zero column (start of content)
            start = None
            for i, s in enumerate(col_sums):
                if s > 0:
                    start = i
                    break
            if start is None:
                return None
            # Find a significant gap (5+ consecutive empty columns) after content
            consecutive_zeros = 0
            min_gap = 5
            for i, s in enumerate(col_sums[start:]):
                if s == 0:
                    consecutive_zeros += 1
                    if consecutive_zeros >= min_gap:
                        return start + i - min_gap + 1
                else:
                    consecutive_zeros = 0
            return len(col_sums)

        lines = self.lines_pos
        offsets = [strip(self.crop_image(mask, i)) for i in lines]

        # Crop from start to where content ends
        stripped = [
            ((line[0][0], line[0][1]), (line[1][0], s))
            for line, s in zip(lines, offsets)
        ]

        return stripped


class ScoreFrame(BaseFrame):
    @cached_property
    def sides_pos(self) -> tuple[Rect, Rect]:
        """Split the score frame into left and right player regions.

        The score frame layout is: [P1 NEXT + Score] [Center Labels] [P2 Score + NEXT]
        The player regions are roughly the outer 42% on each side.
        """
        height = self.image.shape[0]
        width = self.image.shape[1]

        # Player regions are approximately 42% of width on each side
        # This leaves ~16% for center labels (SCORE, LINES, LEVEL)
        player_width_ratio = 0.42
        end_left = int(width * player_width_ratio)
        start_right = int(width * (1 - player_width_ratio))

        return (
            ((0, 0), (height, end_left)),
            ((0, start_right), (height, width)),
        )

    def get_sides(self, roi_ref: RoiRef) -> tuple[LeftScoreFrame, RightScoreFrame]:
        left, right = self.sides_pos
        return LeftScoreFrame(self.crop(left), roi_ref), RightScoreFrame(
            self.crop(right), roi_ref
        )


class PlayerScreen:
    score_frame: SideScoreFrame
    screen: np.array

    def __init__(self, score_frame: SideScoreFrame, screen: np.array):
        self.score_frame = score_frame
        self.screen = screen

    @property
    def is_game_over(self) -> bool:
        return find_game_over(self.screen)


class Frame(BaseFrame):
    """Frame for 1080p input."""

    def __init__(self, image: np.array):
        super().__init__(image)

    def get_score_frame(self) -> ScoreFrame:
        return ScoreFrame(self.crop(self.score_pos))

    def get_player_screens(self, roi_ref: RoiRef):
        score_frame = self.get_score_frame()
        sides = score_frame.get_sides(roi_ref)

        return (
            PlayerScreen(sides[0], self.crop(self.left_screen_pos)),
            PlayerScreen(sides[1], self.crop(self.right_screen_pos)),
        )

    @cached_property
    def arc_pos(self) -> Rect:
        mid = self.image.shape[0] // 2, self.image.shape[1] // 2
        for n, line in enumerate(self.image[mid[0] :: -1]):
            if tuple(line[mid[1]]) != (0, 0, 0):
                top_internal = mid[0] - n
                break
        else:
            raise Exception("Top internal not found")

        for n, line in enumerate(self.image[top_internal::-1]):
            if tuple(line[mid[1]]) == (0, 0, 0):
                top = top_internal - n + 1
                break
        else:
            raise Exception("Top external not found")

        for i in range(mid[1], 0, -1):
            if tuple(self.image[top, i]) == (0, 0, 0):
                left = i
                break
        else:
            raise Exception("top_external_left not found")

        for i in range(mid[1], self.image.shape[1]):
            if tuple(self.image[top, i]) == (0, 0, 0):
                right = i
                break
        else:
            raise Exception("top_external_right not found")

        return (top, left), (self.image.shape[1], right)

    @cached_property
    def score_pos(self) -> Rect:
        mid = self.image.shape[0] // 2, self.image.shape[1] // 2
        arc = self.arc_pos
        top = arc[0][0]
        for n, line in enumerate(self.image[top - 1 :: -1]):
            if tuple(line[mid[1]]) != (0, 0, 0):
                external_bottom = top - n - 1
                break
        else:
            raise Exception("Frame top not found")

        for n, line in enumerate(self.image[external_bottom::-1]):
            if tuple(line[mid[1]]) == (0, 0, 0):
                internal_bottom = external_bottom - n + 1
                break
        else:
            raise Exception("Frame bottom not found")

        return (0, 0), (internal_bottom, self.image.shape[1])

    @cached_property
    def left_screen_pos(self) -> Rect:
        arc_pos = self.arc_pos
        return ((arc_pos[0][0], 0), (self.image.shape[0], arc_pos[0][1]))

    @cached_property
    def right_screen_pos(self):
        arc_pos = self.arc_pos
        return (
            (arc_pos[0][0], arc_pos[1][1]),
            (self.image.shape[0], self.image.shape[1]),
        )

    @cached_property
    def is_paused(self):
        arc = self.crop(self.arc_pos)
        shape = arc.shape
        arc = self.crop_image(
            arc,
            ((0, shape[1] // 10), (shape[0], shape[1] - shape[1] // 10)),
        )

        lower = np.array([0, 0, 200])
        upper = np.array([50, 50, 255])
        mask = cv2.inRange(arc, lower, upper)

        return bool(mask.any())

    @cached_property
    def is_two_player(self) -> bool:
        """Check if this is a 2-player game by looking for NEXT labels on both sides."""
        try:
            score_frame = self.crop(self.score_pos)
            width = score_frame.shape[1]
            # Check left 1/4 and right 1/4 for NEXT label (blue text)
            left_side = score_frame[:, : width // 4]
            right_side = score_frame[:, 3 * width // 4 :]

            left_mask = cv2.inRange(left_side, (0, 0, 150), (100, 100, 255))
            right_mask = cv2.inRange(right_side, (0, 0, 150), (100, 100, 255))

            # Both sides must have NEXT labels for 2-player game
            return cv2.countNonZero(left_mask) > 50 and cv2.countNonZero(right_mask) > 50
        except Exception:
            return False

    @cached_property
    def is_game(self) -> bool:
        """Check if this is a 2-player game (only 2-player games are supported)."""
        return self.is_two_player

    @classmethod
    def strip(cls, frame: np.ndarray):
        return cls(strip_frame(frame))
