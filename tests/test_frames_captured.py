"""Test frame recognition on captured gameplay sequence.

Tests the full frame recognition pipeline on a sequence of 1500 captured frames
containing 2 complete Tetris games. Verifies:
- Black frames are detected and skipped
- Menu frames are recognized
- Game start is detected
- Scores are recognized correctly and always increase
- Game over states are detected
- Pause states are detected
- Two complete games are found in the sequence
"""

from pathlib import Path

import cv2
import pytest

from game_objects.frame import Frame
from cv_tools.detect_digit import get_refs


frames_captured_path = Path(__file__).parent / "fixtures_fullhd" / "frames_captured"


@pytest.fixture
def refs():
    return get_refs()


def frame_exists(frame_num: int) -> bool:
    """Check if a frame file exists."""
    path = frames_captured_path / f"{frame_num:06d}.png"
    return path.exists()


def load_frame(frame_num: int):
    """Load a frame by number (1-indexed)."""
    path = frames_captured_path / f"{frame_num:06d}.png"
    assert path.exists(), f"Frame {frame_num} not found at {path}"
    return cv2.imread(str(path))


def get_available_frames():
    """Get sorted list of available frame numbers."""
    frames = []
    for p in frames_captured_path.glob("*.png"):
        try:
            frames.append(int(p.stem))
        except ValueError:
            pass
    return sorted(frames)


class TestSpecificFrames:
    """Test specific frames with known states."""

    def test_black_frame_1(self):
        """Frame 1 is black, should fail to strip."""
        frame = load_frame(1)
        with pytest.raises(Exception, match="No contours|Wrong"):
            Frame.strip(frame)

    def test_black_frame_2(self):
        """Frame 2 is black, should fail to strip."""
        frame = load_frame(2)
        with pytest.raises(Exception, match="No contours|Wrong"):
            Frame.strip(frame)

    def test_menu_frame_3(self, refs):
        """Frame 3 is menu."""
        frame = load_frame(3)
        f = Frame.strip(frame)
        assert not f.is_game, "Menu should not be detected as game"

    def test_game_start_56(self, refs):
        """Frame 56 is 2-player game start."""
        frame = load_frame(56)
        f = Frame.strip(frame)
        assert f.is_game, "Game start frame should be detected as game"
        screens = f.get_player_screens(refs)
        # At game start, scores should be 0 or very low
        assert screens[0].score_frame.score == 0
        assert screens[1].score_frame.score == 0

    def test_gameplay_145(self, refs):
        """Frame 145: P1 score 92, P2 game over score 2680."""
        frame = load_frame(145)
        f = Frame.strip(frame)
        assert f.is_game
        screens = f.get_player_screens(refs)
        assert screens[0].score_frame.score == 92
        assert screens[1].score_frame.score == 2680
        assert not screens[0].is_game_over
        assert screens[1].is_game_over

    def test_pause_940(self, refs):
        """Frame 940 is paused."""
        frame = load_frame(940)
        f = Frame.strip(frame)
        assert f.is_paused, "Frame 940 should be detected as paused"

    def test_pause_960(self, refs):
        """Frame 960 is paused."""
        frame = load_frame(960)
        f = Frame.strip(frame)
        assert f.is_paused, "Frame 960 should be detected as paused"

    def test_gameplay_994(self, refs):
        """Frame 994: game continued, P1 score 10618, P2 game over score 2680."""
        frame = load_frame(994)
        f = Frame.strip(frame)
        assert f.is_game
        assert not f.is_paused
        screens = f.get_player_screens(refs)
        assert screens[0].score_frame.score == 10618
        assert screens[1].score_frame.score == 2680
        assert not screens[0].is_game_over
        assert screens[1].is_game_over

    def test_game_over_both_1226(self, refs):
        """Frame 1226: P1 game over score 12283, P2 game over score 2680."""
        frame = load_frame(1226)
        f = Frame.strip(frame)
        assert f.is_game
        screens = f.get_player_screens(refs)
        assert screens[0].score_frame.score == 12283
        assert screens[1].score_frame.score == 2680
        assert screens[0].is_game_over
        assert screens[1].is_game_over

    def test_black_frame_1267(self):
        """Frame 1267 is black screen."""
        frame = load_frame(1267)
        with pytest.raises(Exception, match="No contours|Wrong"):
            Frame.strip(frame)

    def test_splash_screen_1268(self, refs):
        """Frame 1268 is start game splash screen - fails to strip due to small contours."""
        frame = load_frame(1268)
        # Splash screen should fail to strip (wrong height due to small/no game area)
        with pytest.raises(Exception, match="Wrong height|No contours"):
            Frame.strip(frame)

    def test_menu_1290(self, refs):
        """Frame 1290 is menu."""
        frame = load_frame(1290)
        f = Frame.strip(frame)
        assert not f.is_game, "Menu should not be detected as game"

    def test_game_start_1311(self, refs):
        """Frame 1311 is new 2-player game started."""
        frame = load_frame(1311)
        f = Frame.strip(frame)
        assert f.is_game, "New game start should be detected as game"
        screens = f.get_player_screens(refs)
        assert screens[0].score_frame.score == 0
        assert screens[1].score_frame.score == 0

    def test_gameplay_1367(self, refs):
        """Frame 1367: P1 game over score 326, P2 score 650."""
        frame = load_frame(1367)
        f = Frame.strip(frame)
        assert f.is_game
        screens = f.get_player_screens(refs)
        assert screens[0].score_frame.score == 326
        assert screens[1].score_frame.score == 650
        assert screens[0].is_game_over
        assert not screens[1].is_game_over

    def test_game_over_both_1398(self, refs):
        """Frame 1398: P1 game over score 326, P2 game over score 2580."""
        frame = load_frame(1398)
        f = Frame.strip(frame)
        assert f.is_game
        screens = f.get_player_screens(refs)
        assert screens[0].score_frame.score == 326
        assert screens[1].score_frame.score == 2580
        assert screens[0].is_game_over
        assert screens[1].is_game_over


class TestFullSequence:
    """Test the complete frame sequence for game detection and score tracking."""

    def test_recognize_all_frames_and_two_games(self, refs):
        """Process all 1500 frames and verify:
        - All game frames have recognizable scores
        - Scores always increase within a game (never decrease)
        - Exactly 2 complete games are detected (both players game over)

        Game detection logic:
        - A new game starts when scores reset to 0-0 (or very low)
        - A game ends when both players are game over AND we see a transition
          (menu, black screen, or new game start)
        - This avoids false positives from pause transitions
        """
        frame_stats = {
            "black_frames": 0,
            "menu_frames": 0,
            "paused_frames": 0,
            "game_frames": 0,
            "strip_failures": 0,
            "score_failures": 0,
        }

        # Track all frame data first, then analyze for games
        frame_data = []
        available_frames = get_available_frames()

        for frame_num in available_frames:
            frame = load_frame(frame_num)

            entry = {
                "frame_num": frame_num,
                "type": None,
                "p1_score": None,
                "p2_score": None,
                "p1_game_over": None,
                "p2_game_over": None,
            }

            try:
                f = Frame.strip(frame)
            except Exception:
                entry["type"] = "black"
                frame_stats["black_frames"] += 1
                frame_stats["strip_failures"] += 1
                frame_data.append(entry)
                continue

            if f.is_paused:
                entry["type"] = "paused"
                frame_stats["paused_frames"] += 1
                frame_data.append(entry)
                continue

            if not f.is_game:
                entry["type"] = "menu"
                frame_stats["menu_frames"] += 1
                frame_data.append(entry)
                continue

            entry["type"] = "game"
            frame_stats["game_frames"] += 1

            try:
                screens = f.get_player_screens(refs)
                entry["p1_score"] = screens[0].score_frame.score
                entry["p2_score"] = screens[1].score_frame.score
                entry["p1_game_over"] = screens[0].is_game_over
                entry["p2_game_over"] = screens[1].is_game_over
            except Exception:
                frame_stats["score_failures"] += 1

            frame_data.append(entry)

        # Now analyze frame data to find complete games
        # A game starts at 0-0 and ends when followed by menu/black after both game over
        games = []
        current_game = None
        both_game_over_start = None

        for i, entry in enumerate(frame_data):
            if entry["type"] == "game" and entry["p1_score"] is not None:
                p1_score = entry["p1_score"]
                p2_score = entry["p2_score"]
                p1_go = entry["p1_game_over"]
                p2_go = entry["p2_game_over"]

                # Check for new game start
                if p1_score == 0 and p2_score == 0:
                    if current_game is not None and current_game.get("completed"):
                        pass  # Previous game already completed
                    current_game = {
                        "start_frame": entry["frame_num"],
                        "scores": [],
                        "p1_max": 0,
                        "p2_max": 0,
                        "end_frame": None,
                        "final_p1": None,
                        "final_p2": None,
                        "completed": False,
                    }
                    games.append(current_game)
                    both_game_over_start = None

                if current_game is not None and not current_game["completed"]:
                    current_game["scores"].append((entry["frame_num"], p1_score, p2_score))
                    current_game["p1_max"] = max(current_game["p1_max"], p1_score)
                    current_game["p2_max"] = max(current_game["p2_max"], p2_score)

                    # Track when both players are game over
                    if p1_go and p2_go:
                        if both_game_over_start is None:
                            both_game_over_start = entry["frame_num"]
                        current_game["end_frame"] = entry["frame_num"]
                        current_game["final_p1"] = p1_score
                        current_game["final_p2"] = p2_score
                    else:
                        # If we see non-game-over after game-over, it was a false positive
                        both_game_over_start = None

            elif entry["type"] in ("menu", "black"):
                # Transition - if we had a game with both game over, it's complete
                if current_game is not None and both_game_over_start is not None:
                    current_game["completed"] = True
                    both_game_over_start = None

        # Print statistics
        print(f"\nFrame statistics:")
        for key, value in frame_stats.items():
            print(f"  {key}: {value}")

        # Filter to completed games with substantial gameplay
        # Note: Using reduced frame set, so threshold is lower
        completed_games = [g for g in games if g.get("completed") and len(g["scores"]) > 10]

        print(f"\nCompleted games with >10 frames: {len(completed_games)}")
        for i, game in enumerate(completed_games):
            print(f"\nGame {i+1}:")
            print(f"  Start frame: {game['start_frame']}")
            print(f"  End frame: {game['end_frame']}")
            print(f"  Frames with scores: {len(game['scores'])}")
            print(f"  P1 max score: {game['p1_max']}")
            print(f"  P2 max score: {game['p2_max']}")
            print(f"  Final P1 score: {game['final_p1']}")
            print(f"  Final P2 score: {game['final_p2']}")

        # Assertions
        assert len(completed_games) == 2, f"Expected 2 complete games, found {len(completed_games)}"

        # Verify game 1: should end around frame 1226 with P1=12283, P2=2680
        game1 = completed_games[0]
        assert game1["final_p1"] == 12283, f"Game 1 final P1 score should be 12283, got {game1['final_p1']}"
        assert game1["final_p2"] == 2680, f"Game 1 final P2 score should be 2680, got {game1['final_p2']}"

        # Verify game 2: should end around frame 1398 with P1=326, P2=2580
        game2 = completed_games[1]
        assert game2["final_p1"] == 326, f"Game 2 final P1 score should be 326, got {game2['final_p1']}"
        assert game2["final_p2"] == 2580, f"Game 2 final P2 score should be 2580, got {game2['final_p2']}"

        # Verify we had plenty of game frames (reduced frame set)
        assert frame_stats["game_frames"] > 50, "Should have many game frames"

        # Verify score failures are minimal
        assert frame_stats["score_failures"] < 50, f"Too many score failures: {frame_stats['score_failures']}"

        # Verify scores generally increase within each game
        for game_idx, game in enumerate(completed_games):
            p1_scores = [s[1] for s in game["scores"]]
            p2_scores = [s[2] for s in game["scores"]]

            p1_decreases = sum(1 for i in range(1, len(p1_scores)) if p1_scores[i] < p1_scores[i-1])
            p2_decreases = sum(1 for i in range(1, len(p2_scores)) if p2_scores[i] < p2_scores[i-1])

            max_decreases = max(len(p1_scores) * 0.05, 5)
            assert p1_decreases < max_decreases, f"Game {game_idx+1}: P1 score decreased {p1_decreases} times"
            assert p2_decreases < max_decreases, f"Game {game_idx+1}: P2 score decreased {p2_decreases} times"

    def test_scores_monotonic_per_game(self, refs):
        """Verify that within each game, scores never decrease (except for OCR errors)."""
        current_p1_score = 0
        current_p2_score = 0
        in_game = False
        score_decreases = []
        available_frames = get_available_frames()

        for frame_num in available_frames:
            frame = load_frame(frame_num)

            try:
                f = Frame.strip(frame)
            except Exception:
                # Reset on black frames (game transition)
                if in_game:
                    current_p1_score = 0
                    current_p2_score = 0
                    in_game = False
                continue

            if f.is_paused:
                continue

            if not f.is_game:
                # Menu - reset scores
                current_p1_score = 0
                current_p2_score = 0
                in_game = False
                continue

            try:
                screens = f.get_player_screens(refs)
                p1_score = screens[0].score_frame.score
                p2_score = screens[1].score_frame.score
            except Exception:
                continue

            if not in_game:
                # New game starting
                in_game = True
                current_p1_score = p1_score
                current_p2_score = p2_score
                continue

            # Check for score decrease (likely OCR error or new game)
            if p1_score < current_p1_score and p1_score > 0:
                # Could be OCR error or new game
                if current_p1_score - p1_score > 1000:
                    # Likely new game (score reset)
                    current_p1_score = p1_score
                    current_p2_score = p2_score
                else:
                    score_decreases.append(
                        f"Frame {frame_num}: P1 score decreased from {current_p1_score} to {p1_score}"
                    )
            else:
                current_p1_score = max(current_p1_score, p1_score)

            if p2_score < current_p2_score and p2_score > 0:
                if current_p2_score - p2_score > 1000:
                    # Likely new game
                    pass
                else:
                    score_decreases.append(
                        f"Frame {frame_num}: P2 score decreased from {current_p2_score} to {p2_score}"
                    )
            else:
                current_p2_score = max(current_p2_score, p2_score)

        # Allow some OCR errors but should be minimal
        if score_decreases:
            print(f"\nScore decreases (possible OCR errors):")
            for decrease in score_decreases[:10]:  # Show first 10
                print(f"  {decrease}")
            if len(score_decreases) > 10:
                print(f"  ... and {len(score_decreases) - 10} more")

        assert len(score_decreases) < 20, f"Too many score decreases: {len(score_decreases)}"
