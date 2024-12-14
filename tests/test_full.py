from pathlib import Path

import cv2
import pytest

from cv_tools import strip_frame
from cv_tools.detect_digit import get_refs
from cv_tools.split_img import split_img
from game_objects.player import Player

fixtures_path = Path(__file__).parent.resolve() / "fixtures"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "img_name,expected", [("test_00145.png", [19, 8]), ("test_00164.png", [27, 10])]
)
async def test_image_1(img_name, expected):
    frame = cv2.imread(str(fixtures_path / img_name))
    _frame = strip_frame(frame)
    frames = split_img(_frame)

    refs = get_refs()

    players = [Player(refs), Player(refs, reverse=True)]
    for p, f in zip(players, frames):
        p.parse_frame(f)

    assert expected == [p.score for p in players]


@pytest.mark.asyncio
async def test_image_2():
    frame = cv2.imread(str(fixtures_path / "test_00000.png"))
    error = None
    try:
        _frame = strip_frame(frame)
    except Exception as e:
        error = e

    assert error is not None


@pytest.mark.asyncio
async def test_image_dance():
    frame = cv2.imread(str(fixtures_path / "test_dance.png"))
    _frame = strip_frame(frame)
    frames = split_img(_frame)

    refs = get_refs()

    players = [Player(refs), Player(refs, reverse=True)]
    for p, f in zip(players, frames):
        p.parse_frame(f)

    assert not any(p.game_over for p in players)
    assert players[0].score == 1314
    assert players[1].score == 426


@pytest.mark.asyncio
async def test_image_end():
    frame = cv2.imread(str(fixtures_path / "test_end.png"))
    _frame = strip_frame(frame)
    frames = split_img(_frame)

    refs = get_refs()

    p = Player(refs)
    p.parse_frame(frames[0])

    assert p.game_over
    assert p.score == 129
