from functools import cached_property

import cv2
import numpy as np

from cv_tools import strip_frame
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
        mid = self.image.shape[0] // 2
        mask = self.mask()
        line = self.mid_line(mask)

        start_top = None
        for n, l in enumerate(line[:][mid::-1]):
            if start_top is None:
                if l[0] != 0:
                    start_top = mid - n + 1
            else:
                if l[0] == 0:
                    end_top = mid - n
                    break
        else:
            raise Exception("top not found")

        start_bottom = None
        for n, l in enumerate(line[:][mid:]):
            if start_bottom is None:
                if l[-1] != 0:
                    start_bottom = mid + n - 1
            else:
                if l[-1] == 0:
                    end_bottom = mid + n
                    break
        else:
            raise Exception("bottom not found")

        return (
            ((0, 0), (end_top, self.image.shape[1])),
            ((start_top, 0), (start_bottom, self.image.shape[1])),
            ((end_bottom, 0), (self.image.shape[0], self.image.shape[1])),
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
            for n, p in enumerate(image[-1][::-1]):
                if p != 0:
                    return image.shape[1] - n

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

        # save_image("mask.png", mask)

        def strip(image: np.array) -> int:
            for n, p in enumerate(image[-1]):
                if p != 0:
                    return n

        lines = self.lines_pos
        # for n, i in enumerate(lines):
        #     save_image(f"{n}.png", self.crop_image(mask, i))

        offsets = [strip(self.crop_image(mask, i)) for i in lines]

        stripped = [
            ((line[0][0], line[0][1]), (line[1][0], s))
            for line, s in zip(lines, offsets)
        ]

        return stripped


class ScoreFrame(BaseFrame):
    @cached_property
    def sides_pos(self) -> tuple[Rect, Rect]:
        sf = self.image
        mid = sf.shape[1] // 2

        mask = self.mask()
        line = mask[-1]

        # save_image("mask.png", mask)

        start_left = None
        for i in range(mid, 0, -1):
            if start_left is None:
                if line[i] != 0:
                    start_left = i
                    continue
            else:
                if line[i] == 0:
                    end_left = i
                    break
        else:
            raise Exception("left not found")

        start_right = None
        for i in range(mid, mask.shape[1]):
            if start_right is None:
                if line[i] != 0:
                    start_right = i
                    continue
            else:
                if line[i] == 0:
                    end_right = i
                    break
        else:
            raise Exception("right not found")

        # save_image("mask2.png", self.crop(((0, 0), (self.image.shape[0], end_left + 1))))

        return (
            ((0, 0), (self.image.shape[0], end_left + 1)),
            ((0, end_right), (self.image.shape[0], self.image.shape[1])),
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
                # save_image("top_internal.png", self.data[top_internal:, :])
                break
        else:
            raise Exception("Top internal not found")

        for n, line in enumerate(self.image[top_internal::-1]):
            if tuple(line[mid[1]]) == (0, 0, 0):
                top = top_internal - n + 1
                # save_image("top_external.png", self.data[top:, :])
                break
        else:
            raise Exception("Top external not found")

        for i in range(mid[1], 0, -1):
            if tuple(self.image[top, i]) == (0, 0, 0):
                left = i
                # save_image("top_left.png", self.data[top:, :left])
                break
        else:
            raise Exception("top_external_left not found")

        for i in range(mid[1], self.image.shape[1]):
            if tuple(self.image[top, i]) == (0, 0, 0):
                right = i
                # save_image("top_right.png", self.data[top:, right:])
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
                # save_image("frame.png", self.data[:frame_bottom, :])
                break
        else:
            raise Exception("Frame top not found")

        for n, line in enumerate(self.image[external_bottom::-1]):
            if tuple(line[mid[1]]) == (0, 0, 0):
                internal_bottom = external_bottom - n + 1
                # save_image("frame.png", self.data[:internal_bottom, :])
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
        # save_image("arc.png", arc)

        lower = np.array([0, 0, 200])
        upper = np.array([50, 50, 255])
        mask = cv2.inRange(arc, lower, upper)
        # save_image("mask.png", mask)

        return bool(mask.any())

    @cached_property
    def is_game(self) -> bool:
        arc = self.crop(self.arc_pos)
        bottom = self.crop_image(
            arc,
            (
                (arc.shape[0] // 2, arc.shape[1] // 2),
                (-1, -1),
            ),
        )
        return bool(bottom.any())

    @classmethod
    def strip(cls, frame: np.ndarray):
        return cls(strip_frame(frame))
