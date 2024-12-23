from pathlib import Path

import cv2
import pytest

from cv_tools.detect_digit import get_refs

fixtures_path = Path(__file__).parent.resolve() / "fixtures"


@pytest.fixture
def dummy2_message_encrypted(dummy2_message):
    return dummy2_message[::-1]


@pytest.fixture
def refs():
    return get_refs()


@pytest.fixture
def load_image():
    def _load_image(name):
        p = fixtures_path / name
        assert p.exists()
        return cv2.imread(str(p))

    return _load_image
