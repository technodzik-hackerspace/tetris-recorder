import pytest

from game_objects.frame import Frame
from game_objects.player import Player


@pytest.mark.parametrize(
    "img_name,expected",
    [
        ("game_started_multi.png", [0, 0]),
        ("326_2580.png", [326, 2580]),
        ("12283_2680.png", [12283, 2680]),
    ],
)
def test_player_scores(img_name, expected, refs, load_image):
    frame = Frame.strip(load_image(img_name))

    players = [Player(), Player()]
    for p, screen in zip(players, frame.get_player_screens(refs)):
        p.parse_frame(screen)

    assert expected == [p.score for p in players]


@pytest.mark.parametrize(
    "img_name,expected",
    [
        ("game_over_both.png", [(True, 12283), (True, 2680)]),
        ("game_over_solo.png", [(True, 326), (False, 1750)]),
        ("game_over_right.png", [(False, 156), (True, 2680)]),
    ],
)
def test_game_over(img_name, expected, refs, load_image):
    frame = Frame.strip(load_image(img_name))

    players = [Player(), Player()]
    for p, screen in zip(players, frame.get_player_screens(refs)):
        p.parse_frame(screen)

    assert [(p.game_over, p.score) for p in players] == expected
