import asyncio
from asyncio import sleep
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from bot import send_video_to_telegram
from config import settings
from cv_tools.frame_generator import frame_generator
from game_objects.game import Game, GameState
from utils.dirs import clean_dir, frames_path, regions_path, videos_path
from utils.ffmpeg_tools import create_video


class _Game(Game):
    frame_number = 0
    recording = False

    async def on_score_change(self):
        score = "/".join(map(str, self.score))
        print(f"Score: {score} frame: {self.frame_number}")

    async def on_game_start(self, multiplayer: bool):
        await super().on_game_start(multiplayer)
        self.frame_number = 0

        t = ["Singleplayer", "Multiplayer"][multiplayer]

        print(f"{t} game started")

    async def on_game_end(self):
        await super().on_game_end()

        score = "/".join(map(str, self.score))
        print(f"Final score: {score}")

        if self.recording:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            video_path = videos_path / f"game_{timestamp}.mp4"
            create_video(video_path, framerate=settings.fps)
            print(f"Video created: {video_path}")

            score = "/".join(map(str, self.score))
            await send_video_to_telegram(video_path, caption=f"Score: {score}")

        clean_dir(frames_path)
        clean_dir(regions_path)

    async def on_frame(self, frame: np.ndarray):
        self.frame_number += 1

        if self.state == GameState.STARTED and self.recording:
            cv2.imwrite(
                str(frames_path / f"frame_{self.frame_number:05d}.png"),
                frame,
            )

        await super().on_frame(frame)


async def main():
    game = _Game()
    image_device = Path(settings.image_device)

    while True:
        for frame in frame_generator(image_device):
            frame_start = datetime.utcnow()

            await game.feed_frame(frame)

            # 10 fps
            spent_time = datetime.utcnow() - frame_start
            await sleep(max(0.0, (1 / settings.fps) - spent_time.total_seconds()))

        # Pause for a moment before starting a new recording
        await sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
