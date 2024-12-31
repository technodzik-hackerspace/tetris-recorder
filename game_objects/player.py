from typing import Optional

from aiogram.types import User

from game_objects.frame import PlayerScreen
from utils.get_player_name import get_user_name


class Player:
    score: Optional[int] = None
    game_over = False

    def __init__(self, user: User | None = None):
        self.user = user

    @property
    def name(self):
        if self.user:
            return get_user_name(self.user)
        return "Player"

    def parse_frame(self, frame_score: PlayerScreen):
        self.score = frame_score.score_frame.score
        if not self.game_over:
            self.game_over = frame_score.is_game_over
