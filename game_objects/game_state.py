from dataclasses import dataclass, field
from enum import Enum, auto

from game_objects.frame_info import FrameInfo


class GameState(Enum):
    """Game state machine states."""

    NOT_TETRIS = auto()  # Black/invalid frame
    MENU = auto()  # In tetris menu
    GAME = auto()  # Active 2-player gameplay
    GAME_OVER = auto()  # Both players finished


@dataclass
class GameStateMachine:
    """State machine for tracking Tetris game progression.

    Tracks state transitions and ensures video is only posted for valid games
    that went through: MENU -> GAME -> GAME_OVER

    Attributes:
        state: Current game state
        last_p1_score: Last known P1 score (for reset detection)
        last_p2_score: Last known P2 score (for reset detection)
        valid_game_started: True if game started from MENU with 0-0 scores
        video_ready: True when a video should be posted
        final_p1_score: Final P1 score when game ended
        final_p2_score: Final P2 score when game ended
        game_over_detected: True when both players have game over (still recording)
    """

    state: GameState = GameState.NOT_TETRIS
    last_p1_score: int | None = None
    last_p2_score: int | None = None
    valid_game_started: bool = False
    video_ready: bool = False
    final_p1_score: int | None = None
    final_p2_score: int | None = None
    game_over_detected: bool = False

    def update(self, info: FrameInfo) -> tuple[GameState, GameState]:
        """Update the state machine with a new frame classification.

        Args:
            info: Classification result from FrameClassifier

        Returns:
            Tuple of (old_state, new_state)
        """
        old_state = self.state

        # Handle invalid/black frames
        if not info.is_tetris:
            # If game over was detected and we get a black frame, finalize the game
            if self.state == GameState.GAME and self.game_over_detected:
                self.state = GameState.GAME_OVER
                self.video_ready = self.valid_game_started
                return old_state, self.state
            self.state = GameState.NOT_TETRIS
            return old_state, self.state

        # Handle paused frames - stay in current state
        if info.is_paused:
            return old_state, self.state

        # Handle menu/non-game frames
        if info.in_menu or not info.in_game:
            if self.state == GameState.GAME:
                # If game over was detected and we're now in menu, finalize the game
                if self.game_over_detected:
                    self.state = GameState.GAME_OVER
                    self.video_ready = self.valid_game_started
                    return old_state, self.state
                # Otherwise, stay in GAME state to not lose recording
                pass
            else:
                self.state = GameState.MENU
            return old_state, self.state

        # We're in a 2-player game
        if not info.has_valid_scores:
            # Can't read scores - stay in current state
            return old_state, self.state

        # Check for score reset (new game starting)
        if self.state == GameState.GAME and self._is_score_reset(info):
            # A new game started mid-recording
            self.video_ready = True
            self.final_p1_score = self.last_p1_score
            self.final_p2_score = self.last_p2_score
            # Reset for new game tracking
            self.valid_game_started = True
            self.last_p1_score = info.p1_score
            self.last_p2_score = info.p2_score
            self.state = GameState.GAME_OVER
            return old_state, self.state

        # Check for game start (0-0 scores from menu)
        if self.state in (GameState.NOT_TETRIS, GameState.MENU) and info.scores_are_zero:
            self.state = GameState.GAME
            self.valid_game_started = True
            self.last_p1_score = 0
            self.last_p2_score = 0
            return old_state, self.state

        # Check for mid-game join (non-zero scores from menu)
        if self.state in (GameState.NOT_TETRIS, GameState.MENU) and not info.scores_are_zero:
            # If both players already have game over, this is a game over screen, not a new game
            if info.both_game_over:
                self.state = GameState.MENU
                return old_state, self.state
            # Joining mid-game - don't mark as valid
            self.state = GameState.GAME
            self.valid_game_started = False
            self.last_p1_score = info.p1_score
            self.last_p2_score = info.p2_score
            return old_state, self.state

        # Update scores during gameplay
        if self.state == GameState.GAME:
            self.last_p1_score = info.p1_score
            self.last_p2_score = info.p2_score

            # Check for game over - mark it but keep recording
            if info.both_game_over and not self.game_over_detected:
                self.game_over_detected = True
                self.final_p1_score = info.p1_score
                self.final_p2_score = info.p2_score
                # Stay in GAME state to continue recording game over frames

        return old_state, self.state

    def _is_score_reset(self, info: FrameInfo) -> bool:
        """Check if scores reset to 0-0 (new game started)."""
        if not info.scores_are_zero:
            return False
        # Only count as reset if we had non-zero scores before
        return (
            self.last_p1_score is not None
            and self.last_p2_score is not None
            and (self.last_p1_score > 0 or self.last_p2_score > 0)
        )

    def acknowledge_game_over(self) -> None:
        """Acknowledge that the game over was processed (video sent).

        Call this after processing the video to reset for the next game.
        """
        self.video_ready = False
        self.state = GameState.MENU
        self.valid_game_started = False
        self.last_p1_score = None
        self.last_p2_score = None
        self.final_p1_score = None
        self.final_p2_score = None
        self.game_over_detected = False

    def reset(self) -> None:
        """Fully reset the state machine to initial state."""
        self.state = GameState.NOT_TETRIS
        self.last_p1_score = None
        self.last_p2_score = None
        self.valid_game_started = False
        self.video_ready = False
        self.final_p1_score = None
        self.final_p2_score = None
        self.game_over_detected = False
