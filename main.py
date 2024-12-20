import asyncio
from asyncio import sleep
from datetime import datetime
from pathlib import Path

import cv2

from bot import send_video_to_telegram
from config import settings
from cv_tools.detect_digit import get_refs
from cv_tools.frame_generator import frame_generator
from cv_tools.score_detect import get_score
from cv_tools.split_img import split_img
from cv_tools.strip_frame import strip_frame
from game_objects.player import Player
from utils.dirs import clean_dir, frames_path, regions_path, videos_path
from utils.ffmpeg_tools import create_video


async def main(recording=False):
    roi_ref = get_refs()
    image_device = Path(settings.image_device)

    while True:
        game_start = False

        players: list[Player] = []
        last_score = [None, None]

        clean_dir(frames_path)
        clean_dir(regions_path)

        for frame_number, frame in enumerate(frame_generator(image_device)):
            frame_start = datetime.utcnow()

            cv2.imwrite(
                str(frames_path / f"test_{frame_number:05d}.png"),
                frame,
            )

            try:
                _frame = strip_frame(frame)
            except Exception as e:
                continue

            cv2.imwrite(
                str(frames_path / f"frame_{frame_number:05d}.png"),
                cv2.resize(_frame, (416, 400)),
            )

            frames = split_img(_frame)

            if not game_start:
                try:
                    score1 = get_score(frames[0], roi_ref=roi_ref)
                    score2 = get_score(frames[1], roi_ref=roi_ref, reverse=True)
                except Exception as e:
                    break

                if score1 == 0:
                    if score2 is None:
                        print("Start: single player")
                        players = [Player(roi_ref)]
                        game_start = True
                    elif score2 == 0:
                        print("Start: multi player")
                        players = [Player(roi_ref), Player(roi_ref, reverse=True)]
                        game_start = True
                else:
                    break

            # cv2.imwrite(str(regions_path / f"p1_{frame_number:05d}.png"), f1)
            # cv2.imwrite(str(regions_path / f"p2_{frame_number:05d}.png"), f2)

            for p, f in zip(players, frames):
                p.parse_frame(f)

            if players[0].score is None:
                break

            if last_score != [i.score for i in players]:
                last_score = [i.score for i in players]
                print(f"Score: {last_score} frame: {frame_number}")

            if all(i.game_over for i in players) and game_start is True:
                print(f"Final score: {last_score}")

                if recording:
                    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                    video_path = videos_path / f"game_{timestamp}.mp4"
                    create_video(video_path, framerate=settings.fps)
                    print(f"Video created: {video_path}")
                    if len(players) == 2:
                        caption = f"Score: {players[0].score} - {players[1].score}"
                    else:
                        caption = f"Score: {players[0].score}"
                    await send_video_to_telegram(video_path, caption=caption)

                break

            # 10 fps
            spent_time = datetime.utcnow() - frame_start
            await sleep(max(0.0, (1 / settings.fps) - spent_time.total_seconds()))

        # Pause for a moment before starting a new recording
        await sleep(1)


if __name__ == "__main__":
    asyncio.run(main(recording=True))
