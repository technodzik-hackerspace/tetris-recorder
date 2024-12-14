import pytest


@pytest.fixture
def dummy2_message_encrypted(dummy2_message):
    return dummy2_message[::-1]
