from typing import Optional

import numpy as np

from cv_tools.find_game_over import find_game_over
from cv_tools.score_detect import get_score


class Player:
    score: Optional[int] = None
    game_over = False

    def __init__(self, roi_ref: dict[int, np.array], reverse=False):
        self.reverse = reverse
        self.roi_ref = roi_ref

    def parse_frame(self, frame: np.ndarray):
        self.score = get_score(frame, roi_ref=self.roi_ref, reverse=self.reverse)
        if not self.game_over:
            self.game_over = find_game_over(frame, self.reverse)
