from enum import Enum
from typing import Optional

import numpy as np

from cv_tools import strip_frame
from cv_tools.detect_digit import get_refs
from cv_tools.score_detect import get_score
from cv_tools.split_img import split_img
from game_objects.player import Player


class GameState(str, Enum):
    STARTED = "started"
    GAME_OVER = "game_over"


class Game:
    state: GameState = GameState.GAME_OVER
    players: Optional[list[Player]] = None
    _last_score = None

    def __init__(self):
        self._roi_ref = get_refs()
        self._processors = {
            GameState.STARTED: self.frame_processor_1,
            GameState.GAME_OVER: self.frame_processor_2,
        }

    @property
    def score(self):
        return [i.score for i in self.players]

    async def feed_frame(self, frame: np.ndarray):
        try:
            _frame = strip_frame(frame)
        except Exception as e:
            return

        await self.on_frame(_frame)

    async def frame_processor_1(self, frames: tuple[np.array, np.array]):
        try:
            score1 = get_score(frames[0], roi_ref=self._roi_ref)
            score2 = get_score(frames[1], roi_ref=self._roi_ref, reverse=True)
        except Exception as e:
            return

        if score1 == 0:
            if score2 is None:
                await self.on_game_start(False)
            elif score2 == 0:
                await self.on_game_start(True)

    async def frame_processor_2(self, frames: tuple[np.array, np.array]):
        for p, f in zip(self.players, frames):
            p.parse_frame(f)

        if self.players[0].score is None:
            self.state = GameState.GAME_OVER
            return

        if self._last_score != self.score:
            self._last_score = self.score
            await self.on_score_change()

        if all(i.game_over for i in self.players):
            await self.on_game_end()

    async def on_frame(self, frame: np.ndarray):
        frames = split_img(frame)
        await self._processors[self.state](frames)

    async def on_game_start(self, multiplayer: bool):
        self.state = GameState.STARTED
        self.players = [Player(self._roi_ref)]
        if multiplayer:
            self.players.append(Player(self._roi_ref, reverse=True))

    async def on_score_change(self):
        pass

    async def on_game_end(self):
        self.state = GameState.GAME_OVER
