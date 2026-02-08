import time
from dataclasses import dataclass, field

import numpy as np

from cv_tools.detect_digit import RoiRef
from cv_tools.strip_frame import strip_frame
from game_objects.frame import Frame
from game_objects.frame_info import FrameInfo


@dataclass
class TimingStats:
    """Timing statistics for frame classification."""

    strip_time: float = 0.0
    is_paused_time: float = 0.0
    is_two_player_time: float = 0.0
    score_detect_time: float = 0.0
    total_time: float = 0.0

    def __str__(self) -> str:
        return (
            f"strip={self.strip_time * 1000:.1f}ms, "
            f"pause={self.is_paused_time * 1000:.1f}ms, "
            f"2p={self.is_two_player_time * 1000:.1f}ms, "
            f"score={self.score_detect_time * 1000:.1f}ms, "
            f"total={self.total_time * 1000:.1f}ms"
        )


@dataclass
class CumulativeTimingStats:
    """Cumulative timing statistics across multiple frames."""

    strip_time: float = 0.0
    is_paused_time: float = 0.0
    is_two_player_time: float = 0.0
    score_detect_time: float = 0.0
    total_time: float = 0.0
    frame_count: int = 0

    def add(self, stats: TimingStats):
        self.strip_time += stats.strip_time
        self.is_paused_time += stats.is_paused_time
        self.is_two_player_time += stats.is_two_player_time
        self.score_detect_time += stats.score_detect_time
        self.total_time += stats.total_time
        self.frame_count += 1

    def reset(self):
        self.strip_time = 0.0
        self.is_paused_time = 0.0
        self.is_two_player_time = 0.0
        self.score_detect_time = 0.0
        self.total_time = 0.0
        self.frame_count = 0

    def avg_str(self) -> str:
        if self.frame_count == 0:
            return "no frames"
        n = self.frame_count
        return (
            f"strip={self.strip_time / n * 1000:.1f}ms, "
            f"pause={self.is_paused_time / n * 1000:.1f}ms, "
            f"2p={self.is_two_player_time / n * 1000:.1f}ms, "
            f"score={self.score_detect_time / n * 1000:.1f}ms, "
            f"total={self.total_time / n * 1000:.1f}ms"
        )


class FrameClassifier:
    """Classifies raw video frames and extracts game state information.

    This class encapsulates all CV detection logic and returns an immutable
    FrameInfo object with the classification results.
    """

    def __init__(self, roi_ref: RoiRef):
        """Initialize the classifier with digit reference images.

        Args:
            roi_ref: Reference images for digit template matching
        """
        self.roi_ref = roi_ref
        self.last_timing = TimingStats()
        self.cumulative_timing = CumulativeTimingStats()

    def classify(self, raw_frame: np.ndarray, skip_score: bool = False) -> FrameInfo:
        """Classify a raw video frame and extract game state.

        Args:
            raw_frame: Raw BGR frame from video capture
            skip_score: If True, skip score OCR (still detects game_over)

        Returns:
            FrameInfo with classification results
        """
        total_start = time.perf_counter()
        timing = TimingStats()

        # Try to strip the frame (isolate game area)
        t0 = time.perf_counter()
        try:
            stripped = strip_frame(raw_frame)
        except Exception:
            timing.strip_time = time.perf_counter() - t0
            timing.total_time = time.perf_counter() - total_start
            self.last_timing = timing
            self.cumulative_timing.add(timing)
            # Not a valid tetris frame (black/invalid)
            return FrameInfo(
                is_tetris=False,
                in_menu=False,
                in_game=False,
                game_type=None,
                p1_score=None,
                p2_score=None,
                p1_game_over=False,
                p2_game_over=False,
                is_paused=False,
                raw_frame=raw_frame,
            )
        timing.strip_time = time.perf_counter() - t0

        frame = Frame(stripped)

        # Check if paused (includes bonus detection)
        t0 = time.perf_counter()
        try:
            is_paused = frame.is_paused
        except Exception:
            is_paused = False
        timing.is_paused_time = time.perf_counter() - t0

        if is_paused:
            timing.total_time = time.perf_counter() - total_start
            self.last_timing = timing
            self.cumulative_timing.add(timing)
            return FrameInfo(
                is_tetris=True,
                in_menu=False,
                in_game=False,
                game_type=None,
                p1_score=None,
                p2_score=None,
                p1_game_over=False,
                p2_game_over=False,
                is_paused=True,
                raw_frame=raw_frame,
            )

        # Check if this is a 2-player game
        t0 = time.perf_counter()
        try:
            is_two_player = frame.is_two_player
        except Exception:
            is_two_player = False
        timing.is_two_player_time = time.perf_counter() - t0

        if not is_two_player:
            timing.total_time = time.perf_counter() - total_start
            self.last_timing = timing
            self.cumulative_timing.add(timing)
            # In menu or single player (not supported)
            return FrameInfo(
                is_tetris=True,
                in_menu=True,
                in_game=False,
                game_type=None,
                p1_score=None,
                p2_score=None,
                p1_game_over=False,
                p2_game_over=False,
                is_paused=False,
                raw_frame=raw_frame,
            )

        # Two-player game detected - extract scores and game over status
        p1_score = None
        p2_score = None
        p1_game_over = False
        p2_game_over = False

        t0 = time.perf_counter()
        try:
            screens = frame.get_player_screens(self.roi_ref)
            # Always check game_over status (needed for state machine)
            p1_game_over = screens[0].is_game_over
            p2_game_over = screens[1].is_game_over
            # Only do score OCR if not skipping
            if not skip_score:
                p1_score = screens[0].score_frame.score
                p2_score = screens[1].score_frame.score
        except Exception:
            # Could not detect player screens (transitional frame)
            pass
        timing.score_detect_time = time.perf_counter() - t0

        timing.total_time = time.perf_counter() - total_start
        self.last_timing = timing
        self.cumulative_timing.add(timing)

        return FrameInfo(
            is_tetris=True,
            in_menu=False,
            in_game=True,
            game_type="multi",
            p1_score=p1_score,
            p2_score=p2_score,
            p1_game_over=p1_game_over,
            p2_game_over=p2_game_over,
            is_paused=False,
            raw_frame=raw_frame,
        )
