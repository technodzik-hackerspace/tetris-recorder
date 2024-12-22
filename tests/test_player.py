import cv2
import pytest

from cv_tools import strip_frame
from game_objects.frame import Frame
from game_objects.player import Player
from tests.conftest import fixtures_path


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "img_name,expected",
    [
        ("test_00145.png", [19, 8]),
        ("test_00164.png", [27, 10]),
    ],
)
async def test_image_1(img_name, expected, refs, load_image):
    frame = Frame.strip(load_image(img_name))

    players = [Player(), Player()]
    for p, screen in zip(players, frame.get_player_screens(refs)):
        p.parse_frame(screen)

    assert expected == [p.score for p in players]


@pytest.mark.asyncio
async def test_image_2():
    frame = cv2.imread(str(fixtures_path / "push_start_button.png"))
    error = None
    try:
        _frame = strip_frame(frame)
    except Exception as e:
        error = e

    assert error is not None


@pytest.mark.asyncio
async def test_image_dance(refs, load_image):
    frame = Frame.strip(load_image("test_dance.png"))

    players = [Player(), Player()]
    for p, screen in zip(players, frame.get_player_screens(refs)):
        p.parse_frame(screen)

    assert not any(p.game_over for p in players)
    assert players[0].score == 1314
    assert players[1].score == 426


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "img_name,expected",
    [
        ("game_over_both.png", [(True, 242), (True, 243)]),
        ("game_over_solo.png", [(True, 129), (False, None)]),
        ("game_over_right.png", [(False, 121), (True, 243)]),
    ],
)
async def test_solo_game_over(img_name, expected, refs, load_image):
    frame = Frame.strip(load_image(img_name))

    players = [Player(), Player()]
    for p, screen in zip(players, frame.get_player_screens(refs)):
        p.parse_frame(screen)

    assert [(p.game_over, p.score) for p in players] == expected
