from pathlib import Path

import cv2
import pytest

from cv_tools import strip_frame
from cv_tools.detect_digit import get_refs
from cv_tools.split_img import split_img
from player import Player

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
