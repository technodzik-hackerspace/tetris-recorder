import pytest

from game_objects.frame import Frame


@pytest.mark.parametrize(
    "img_name,expected",
    [
        ("game_started_multi.png", ([0, 0, 1], [0, 0, 9])),
        ("326_2580.png", ([326, 0, 1], [2580, 0, 9])),
        ("12283_2680.png", ([12283, 37, 2], [2680, 0, 9])),
        ("game_over_right.png", ([156, 4, 1], [2680, 0, 9])),
        ("game_over_both.png", ([12283, 37, 2], [2680, 0, 9])),
        ("game_over_solo.png", ([326, 0, 1], [1750, 0, 9])),
    ],
)
def test_score_frame(img_name, expected, refs, load_image):
    f = Frame.strip(load_image(img_name))
    score_frame = f.get_score_frame()
    l, r = score_frame.get_sides(refs)

    lt = [l.score, l.lines, l.level]
    rt = [r.score, r.lines, r.level]
    assert (lt, rt) == expected


@pytest.mark.parametrize(
    "img_name,expected",
    [
        ("game_started_multi.png", False),
        ("326_2580.png", False),
        ("12283_2680.png", False),
        ("game_over_both.png", False),
        ("game_over_solo.png", False),
        ("menu.png", False),
    ],
)
def test_is_paused(img_name, expected, load_image):
    f = Frame.strip(load_image(img_name))
    assert f.is_paused == expected


def test_menu(load_image):
    f = Frame.strip(load_image("menu.png"))
    assert not f.is_paused
    assert not f.is_game


@pytest.mark.parametrize(
    "img_name,expected",
    [
        ("game_started_multi.png", True),
        ("326_2580.png", True),
        ("12283_2680.png", True),
        ("game_over_both.png", True),
        ("game_over_solo.png", True),
        ("menu.png", False),
    ],
)
def test_is_game(img_name, expected, load_image):
    f = Frame.strip(load_image(img_name))
    assert f.is_game == expected


@pytest.mark.parametrize(
    "img_name,expected",
    [
        ("game_started_multi.png", (False, False)),
        ("326_2580.png", (True, True)),
        ("12283_2680.png", (True, True)),
        ("game_over_both.png", (True, True)),
        ("game_over_solo.png", (True, False)),
        ("game_over_right.png", (False, True)),
    ],
)
def test_game_over(img_name, expected, load_image, refs):
    f = Frame.strip(load_image(img_name))
    screens = f.get_player_screens(refs)
    assert (screens[0].is_game_over, screens[1].is_game_over) == expected
