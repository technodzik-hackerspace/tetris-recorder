import numpy as np
import pytest

from game_objects.frame_info import FrameInfo
from game_objects.game_state import GameState, GameStateMachine


def make_frame_info(
    is_tetris=True,
    in_menu=False,
    in_game=True,
    game_type="multi",
    p1_score=0,
    p2_score=0,
    p1_game_over=False,
    p2_game_over=False,
    is_paused=False,
):
    """Helper to create FrameInfo objects for testing."""
    return FrameInfo(
        is_tetris=is_tetris,
        in_menu=in_menu,
        in_game=in_game,
        game_type=game_type,
        p1_score=p1_score,
        p2_score=p2_score,
        p1_game_over=p1_game_over,
        p2_game_over=p2_game_over,
        is_paused=is_paused,
        raw_frame=None,
    )


class TestGameStateMachine:
    """Tests for GameStateMachine state transitions."""

    def test_initial_state(self):
        """State machine starts in NOT_TETRIS state."""
        sm = GameStateMachine()
        assert sm.state == GameState.NOT_TETRIS
        assert sm.valid_game_started is False
        assert sm.video_ready is False

    def test_not_tetris_to_menu(self):
        """NOT_TETRIS -> MENU when valid tetris frame in menu detected."""
        sm = GameStateMachine()
        info = make_frame_info(is_tetris=True, in_menu=True, in_game=False)

        old, new = sm.update(info)

        assert old == GameState.NOT_TETRIS
        assert new == GameState.MENU
        assert sm.state == GameState.MENU

    def test_menu_to_game_with_zero_scores(self):
        """MENU -> GAME when 2-player game starts with 0-0 scores."""
        sm = GameStateMachine()
        sm.state = GameState.MENU

        info = make_frame_info(in_game=True, p1_score=0, p2_score=0)
        old, new = sm.update(info)

        assert old == GameState.MENU
        assert new == GameState.GAME
        assert sm.valid_game_started is True

    def test_menu_to_game_mid_game_join(self):
        """MENU -> GAME with non-zero scores marks game as invalid."""
        sm = GameStateMachine()
        sm.state = GameState.MENU

        info = make_frame_info(in_game=True, p1_score=100, p2_score=200)
        old, new = sm.update(info)

        assert old == GameState.MENU
        assert new == GameState.GAME
        assert sm.valid_game_started is False

    def test_game_to_game_over(self):
        """GAME -> GAME_OVER when both players have game over and screen changes to menu."""
        sm = GameStateMachine()
        sm.state = GameState.GAME
        sm.valid_game_started = True
        sm.last_p1_score = 1000
        sm.last_p2_score = 2000

        # Game over detected - stays in GAME to record game over screen
        info = make_frame_info(
            in_game=True,
            p1_score=1000,
            p2_score=2000,
            p1_game_over=True,
            p2_game_over=True,
        )
        old, new = sm.update(info)

        assert old == GameState.GAME
        assert new == GameState.GAME  # Still in GAME, recording game over screen
        assert sm.game_over_detected is True
        assert sm.final_p1_score == 1000
        assert sm.final_p2_score == 2000

        # Screen transitions to menu - now finalize
        menu_info = make_frame_info(is_tetris=True, in_menu=True, in_game=False)
        old, new = sm.update(menu_info)

        assert old == GameState.GAME
        assert new == GameState.GAME_OVER
        assert sm.video_ready is True

    def test_game_over_video_ready_only_for_valid_games(self):
        """video_ready is only True for games that started from MENU."""
        sm = GameStateMachine()
        sm.state = GameState.GAME
        sm.valid_game_started = False  # Mid-game join
        sm.last_p1_score = 1000
        sm.last_p2_score = 2000

        # Game over detected
        info = make_frame_info(
            in_game=True,
            p1_score=1000,
            p2_score=2000,
            p1_game_over=True,
            p2_game_over=True,
        )
        sm.update(info)
        assert sm.game_over_detected is True

        # Screen transitions to menu
        menu_info = make_frame_info(is_tetris=True, in_menu=True, in_game=False)
        sm.update(menu_info)

        assert sm.state == GameState.GAME_OVER
        assert sm.video_ready is False  # Invalid game, no video

    def test_score_reset_triggers_game_over(self):
        """Score reset to 0-0 during GAME triggers GAME_OVER."""
        sm = GameStateMachine()
        sm.state = GameState.GAME
        sm.valid_game_started = True
        sm.last_p1_score = 5000
        sm.last_p2_score = 3000

        info = make_frame_info(in_game=True, p1_score=0, p2_score=0)
        old, new = sm.update(info)

        assert old == GameState.GAME
        assert new == GameState.GAME_OVER
        assert sm.video_ready is True
        assert sm.final_p1_score == 5000
        assert sm.final_p2_score == 3000

    def test_paused_frame_maintains_state(self):
        """Paused frames should not change state."""
        sm = GameStateMachine()
        sm.state = GameState.GAME
        sm.valid_game_started = True

        info = make_frame_info(is_paused=True)
        old, new = sm.update(info)

        assert old == GameState.GAME
        assert new == GameState.GAME
        assert sm.state == GameState.GAME

    def test_invalid_frame_goes_to_not_tetris(self):
        """Invalid/black frames should go to NOT_TETRIS."""
        sm = GameStateMachine()
        sm.state = GameState.MENU

        info = make_frame_info(is_tetris=False, in_game=False)
        old, new = sm.update(info)

        assert old == GameState.MENU
        assert new == GameState.NOT_TETRIS

    def test_acknowledge_game_over_resets_state(self):
        """acknowledge_game_over should reset for next game."""
        sm = GameStateMachine()
        sm.state = GameState.GAME_OVER
        sm.valid_game_started = True
        sm.video_ready = True
        sm.final_p1_score = 1000
        sm.final_p2_score = 2000

        sm.acknowledge_game_over()

        assert sm.state == GameState.MENU
        assert sm.video_ready is False
        assert sm.valid_game_started is False
        assert sm.final_p1_score is None
        assert sm.final_p2_score is None

    def test_reset_goes_to_initial_state(self):
        """reset should return to initial state."""
        sm = GameStateMachine()
        sm.state = GameState.GAME
        sm.valid_game_started = True
        sm.last_p1_score = 1000

        sm.reset()

        assert sm.state == GameState.NOT_TETRIS
        assert sm.valid_game_started is False
        assert sm.last_p1_score is None

    def test_full_valid_game_flow(self):
        """Test a complete valid game flow: MENU -> GAME -> GAME_OVER."""
        sm = GameStateMachine()

        # Start in menu
        menu_info = make_frame_info(is_tetris=True, in_menu=True, in_game=False)
        sm.update(menu_info)
        assert sm.state == GameState.MENU

        # Game starts with 0-0
        start_info = make_frame_info(in_game=True, p1_score=0, p2_score=0)
        sm.update(start_info)
        assert sm.state == GameState.GAME
        assert sm.valid_game_started is True

        # Mid-game scores
        mid_info = make_frame_info(in_game=True, p1_score=5000, p2_score=3000)
        sm.update(mid_info)
        assert sm.state == GameState.GAME
        assert sm.last_p1_score == 5000
        assert sm.last_p2_score == 3000

        # Game over - still recording game over screen
        end_info = make_frame_info(
            in_game=True,
            p1_score=10000,
            p2_score=8000,
            p1_game_over=True,
            p2_game_over=True,
        )
        sm.update(end_info)
        assert sm.state == GameState.GAME  # Still recording
        assert sm.game_over_detected is True
        assert sm.final_p1_score == 10000
        assert sm.final_p2_score == 8000

        # Screen transitions to menu - finalize
        sm.update(menu_info)
        assert sm.state == GameState.GAME_OVER
        assert sm.video_ready is True

    def test_mid_game_join_no_video(self):
        """Test mid-game join flow - should not produce video."""
        sm = GameStateMachine()

        # Menu
        menu_info = make_frame_info(is_tetris=True, in_menu=True, in_game=False)
        sm.update(menu_info)

        # Join mid-game with non-zero scores
        mid_join_info = make_frame_info(in_game=True, p1_score=5000, p2_score=3000)
        sm.update(mid_join_info)
        assert sm.state == GameState.GAME
        assert sm.valid_game_started is False

        # Game over - still recording
        end_info = make_frame_info(
            in_game=True,
            p1_score=10000,
            p2_score=8000,
            p1_game_over=True,
            p2_game_over=True,
        )
        sm.update(end_info)
        assert sm.state == GameState.GAME
        assert sm.game_over_detected is True

        # Screen transitions to menu - finalize
        sm.update(menu_info)
        assert sm.state == GameState.GAME_OVER
        assert sm.video_ready is False  # No video for mid-game join


class TestFrameInfo:
    """Tests for FrameInfo helper properties."""

    def test_both_game_over(self):
        info = make_frame_info(p1_game_over=True, p2_game_over=True)
        assert info.both_game_over is True

        info = make_frame_info(p1_game_over=True, p2_game_over=False)
        assert info.both_game_over is False

    def test_scores_are_zero(self):
        info = make_frame_info(p1_score=0, p2_score=0)
        assert info.scores_are_zero is True

        info = make_frame_info(p1_score=100, p2_score=0)
        assert info.scores_are_zero is False

    def test_has_valid_scores(self):
        info = make_frame_info(p1_score=100, p2_score=200)
        assert info.has_valid_scores is True

        info = make_frame_info(p1_score=None, p2_score=200)
        assert info.has_valid_scores is False
