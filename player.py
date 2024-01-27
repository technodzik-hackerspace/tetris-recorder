from typing import Optional

import numpy as np

from cv_tools.find_game_over import find_game_over
from cv_tools.score_detect import get_score


class Player:
    score: Optional[int] = None
    end = False

    def __init__(self, roi_ref: dict[int, np.array], reverse=False):
        self.reverse = reverse
        self.roi_ref = roi_ref

    def parse_frame(self, frame):
        self.score = get_score(frame, roi_ref=self.roi_ref, reverse=self.reverse)
        if not self.end:
            self.end = find_game_over(frame, self.reverse)
