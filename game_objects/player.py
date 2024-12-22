from typing import Optional

from game_objects.frame import PlayerScreen


class Player:
    score: Optional[int] = None
    game_over = False

    def __init__(self, name="Player"):
        self.name = name

    def parse_frame(self, frame_score: PlayerScreen):
        self.score = frame_score.score_frame.score
        if not self.game_over:
            self.game_over = frame_score.is_game_over
