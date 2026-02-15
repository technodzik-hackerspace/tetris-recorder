import pytest

from game_objects.frame_classifier import FrameClassifier


class TestFrameClassifier:
    """Tests for FrameClassifier."""

    def test_classify_menu(self, load_image, refs):
        """Menu frame should be classified as in_menu."""
        classifier = FrameClassifier(refs)
        frame = load_image("menu.png")
        info = classifier.classify(frame)

        assert info.is_tetris is True
        assert info.in_menu is True
        assert info.in_game is False
        assert info.is_paused is False

    def test_classify_game_started(self, load_image, refs):
        """Game start frame should be classified as in_game with 0-0 scores."""
        classifier = FrameClassifier(refs)
        frame = load_image("game_started_multi.png")
        info = classifier.classify(frame)

        assert info.is_tetris is True
        assert info.in_menu is False
        assert info.in_game is True
        assert info.game_type == "multi"
        assert info.p1_score == 0
        assert info.p2_score == 0
        assert info.p1_game_over is False
        assert info.p2_game_over is False
        assert info.is_paused is False
        assert info.scores_are_zero is True

    def test_classify_mid_game(self, load_image, refs):
        """Mid-game frame should show correct scores."""
        classifier = FrameClassifier(refs)
        frame = load_image("326_2580.png")
        info = classifier.classify(frame)

        assert info.is_tetris is True
        assert info.in_game is True
        assert info.p1_score == 326
        assert info.p2_score == 2580
        assert info.has_valid_scores is True

    def test_classify_game_over_both(self, load_image, refs):
        """Both players game over should be detected."""
        classifier = FrameClassifier(refs)
        frame = load_image("game_over_both.png")
        info = classifier.classify(frame)

        assert info.is_tetris is True
        assert info.in_game is True
        assert info.p1_game_over is True
        assert info.p2_game_over is True
        assert info.both_game_over is True

    def test_classify_game_over_solo(self, load_image, refs):
        """Single player game over - P1 game over, P2 still playing."""
        classifier = FrameClassifier(refs)
        frame = load_image("game_over_solo.png")
        info = classifier.classify(frame)

        assert info.is_tetris is True
        assert info.in_game is True
        assert info.p1_game_over is True
        assert info.p2_game_over is False
        assert info.both_game_over is False

    def test_classify_game_over_right(self, load_image, refs):
        """P2 game over, P1 still playing."""
        classifier = FrameClassifier(refs)
        frame = load_image("game_over_right.png")
        info = classifier.classify(frame)

        assert info.is_tetris is True
        assert info.in_game is True
        assert info.p1_game_over is False
        assert info.p2_game_over is True
        assert info.both_game_over is False

    def test_classify_paused_2p(self, load_image, refs):
        """Paused 2-player game should be classified as in_game and paused."""
        classifier = FrameClassifier(refs)
        frame = load_image("paused_2p.png")
        info = classifier.classify(frame)

        assert info.is_tetris is True
        assert info.in_menu is False
        assert info.in_game is True
        assert info.is_paused is True


@pytest.mark.parametrize(
    "img_name,expected_scores",
    [
        ("game_started_multi.png", (0, 0)),
        ("326_2580.png", (326, 2580)),
        ("12283_2680.png", (12283, 2680)),
        ("game_over_right.png", (156, 2680)),
        ("game_over_both.png", (12283, 2680)),
        ("game_over_solo.png", (326, 1750)),
    ],
)
def test_classifier_scores(img_name, expected_scores, load_image, refs):
    """Test score detection across various game states."""
    classifier = FrameClassifier(refs)
    frame = load_image(img_name)
    info = classifier.classify(frame)

    assert info.p1_score == expected_scores[0]
    assert info.p2_score == expected_scores[1]


@pytest.mark.parametrize(
    "img_name,expected_game_over",
    [
        ("game_started_multi.png", (False, False)),
        ("326_2580.png", (True, True)),
        ("12283_2680.png", (True, True)),
        ("game_over_both.png", (True, True)),
        ("game_over_solo.png", (True, False)),
        ("game_over_right.png", (False, True)),
    ],
)
def test_classifier_game_over(img_name, expected_game_over, load_image, refs):
    """Test game over detection across various game states."""
    classifier = FrameClassifier(refs)
    frame = load_image(img_name)
    info = classifier.classify(frame)

    assert (info.p1_game_over, info.p2_game_over) == expected_game_over
