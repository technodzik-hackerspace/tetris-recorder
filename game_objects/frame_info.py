from dataclasses import dataclass
from typing import Literal

import numpy as np


@dataclass(frozen=True)
class FrameInfo:
    """Immutable classification result for a single video frame.

    Attributes:
        is_tetris: True if this is a valid tetris frame (not black/invalid)
        in_menu: True if in tetris menu (not active gameplay)
        in_game: True if active 2-player gameplay is detected
        game_type: "single" or "multi" if detected, None otherwise
        p1_score: Player 1 score if detectable, None otherwise
        p2_score: Player 2 score if detectable, None otherwise
        p1_game_over: True if player 1 has game over
        p2_game_over: True if player 2 has game over
        is_paused: True if game is paused
        raw_frame: The original frame for recording purposes
    """

    is_tetris: bool
    in_menu: bool
    in_game: bool
    game_type: Literal["single", "multi"] | None
    p1_score: int | None
    p2_score: int | None
    p1_game_over: bool
    p2_game_over: bool
    is_paused: bool
    raw_frame: np.ndarray | None = None

    def __hash__(self):
        # raw_frame is not hashable, so we exclude it
        return hash(
            (
                self.is_tetris,
                self.in_menu,
                self.in_game,
                self.game_type,
                self.p1_score,
                self.p2_score,
                self.p1_game_over,
                self.p2_game_over,
                self.is_paused,
            )
        )

    @property
    def both_game_over(self) -> bool:
        """Check if both players have game over."""
        return self.p1_game_over and self.p2_game_over

    @property
    def scores_are_zero(self) -> bool:
        """Check if both player scores are zero (game start condition)."""
        return self.p1_score == 0 and self.p2_score == 0

    @property
    def has_valid_scores(self) -> bool:
        """Check if both players have detectable scores."""
        return self.p1_score is not None and self.p2_score is not None
