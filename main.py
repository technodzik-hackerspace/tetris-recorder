import asyncio
import logging
from asyncio import sleep
from copy import deepcopy
from datetime import datetime, UTC
from pathlib import Path

from aiogram import Bot

from bot import get_bot, send_video_to_telegram, start_polling
from commitment import player_commitment
from config import settings
from cv_tools.debug import save_image
from cv_tools.detect_digit import get_refs, RoiRef
from cv_tools.frame_generator import frame_generator
from game_objects.frame import Frame
from game_objects.player import Player
from utils.dirs import (
    clean_dir,
    frames_path,
    full_frames_path,
    regions_path,
    videos_path,
)
from utils.ffmpeg_tools import create_video


def utcnow():
    return datetime.now(UTC)


class ILoggerAdapter(logging.LoggerAdapter):
    def __init__(self, logger, extra):
        super().__init__(logger, extra)
        self.env = extra

    def process(self, msg, kwargs):
        msg, kwargs = super().process(msg, kwargs)

        result = deepcopy(kwargs)

        default_kwargs_key = ["exc_info", "stack_info", "extra"]
        custome_key = [k for k in result.keys() if k not in default_kwargs_key]
        result["extra"].update({k: result.pop(k) for k in custome_key})

        return msg, result


def get_frame_logger(name):
    _log = logging.getLogger(name)
    h = logging.StreamHandler()
    h.setFormatter(
        logging.Formatter("%(levelname)s:%(name)s[%(frame_number)s]:%(message)s")
    )
    for i in _log.handlers:
        _log.removeHandler(i)
    _log.addHandler(h)

    _log.setLevel(logging.INFO)

    return _log


async def game_loop(bot: Bot, image_device: Path, roi_ref: RoiRef):
    _log = get_frame_logger("game")

    midgame = False
    pause_started = False
    game_started = False

    players: list[Player] = []
    last_score = [None, None]
    last_game_over = [False, False]

    clean_dir(frames_path)
    clean_dir(full_frames_path)

    for frame_number, frame in enumerate(frame_generator(image_device)):
        await sleep(0)
        log = ILoggerAdapter(_log, {"frame_number": frame_number})

        frame_start = utcnow()

        save_image(full_frames_path / f"{frame_number:06d}.png", frame)

        try:
            f = Frame.strip(frame)
        except Exception as e:
            continue

        if f.is_paused:
            if not pause_started:
                log.info("Pause")
                pause_started = True
            continue
        elif pause_started:
            log.info("Resume")
            pause_started = False

        if not f.is_game:
            continue

        save_image(frames_path / f"{frame_number:06d}.png", f.image)

        screens = f.get_player_screens(roi_ref)

        if not game_started:
            try:
                score1 = screens[0].score_frame.score
                score2 = screens[1].score_frame.score
            except Exception as e:
                clean_dir(frames_path)
                continue

            if score1 == 0:
                if score2 == 0:
                    if player_commitment.p1 and player_commitment.p2:
                        text = f"P1:{player_commitment.p1_name} vs P2:{player_commitment.p2_name}"
                        log.info(f"Start: {text}")

                        await bot.send_message(
                            player_commitment.p1.id, text=f"Game {text} started"
                        )
                        await bot.send_message(
                            player_commitment.p2.id, text=f"Game {text} started"
                        )
                    else:
                        log.info("Start: multi player")

                    players = [
                        Player(player_commitment.p1_name),
                        Player(player_commitment.p2_name),
                    ]
                else:
                    log.info("Start: single player")
                    players = [Player(player_commitment.p1_name)]

                game_started = True
                player_commitment.start()
                midgame = True
            else:
                if midgame is False:
                    midgame = True
                    log.info("Midgame, waiting for start")
                clean_dir(frames_path)
                continue
        else:
            midgame = False

        # print("Frame: ", frame_number)

        for p, screen in zip(players, screens):
            p.parse_frame(screen)

        if players[0].score is None:
            break

        if last_score != [i.score for i in players]:
            last_score = [i.score for i in players]
            log.info(f"Score: {last_score}")

        if last_game_over != [i.game_over for i in players]:
            for go, p in zip(last_game_over, players):
                if go != p.game_over:
                    log.info(f"{p.name} game over: {p.score}")
            last_game_over = [i.game_over for i in players]

        if all(i.game_over for i in players) and game_started is True:
            log.info(f"Final score: {last_score}")

            if len(players) == 2:
                video_path = compile_video()
                log.info(f"Video created: {video_path}")

                if player_commitment.p1:
                    await send_video_to_telegram(
                        bot,
                        chat_id=player_commitment.p1.id,
                        video_path=video_path,
                        caption=get_player_message(players[0], players[1]),
                    )
                if player_commitment.p2:
                    await send_video_to_telegram(
                        bot,
                        chat_id=player_commitment.p2.id,
                        video_path=video_path,
                        caption=get_player_message(players[1], players[0]),
                    )
                player_commitment.clear()
            break

        # 10 fps
        spent_time = utcnow() - frame_start
        await sleep(max(0.0, (1 / settings.fps) - spent_time.total_seconds()))

    # Pause for a moment before starting a new recording
    await sleep(1)


def get_player_message(player: Player, opponent: Player):
    if player.score > opponent.score:
        caption = "You win!"
    elif player.score < opponent.score:
        caption = "You lose!"
    else:
        caption = "Draw!"

    caption += f"\nYour score: {player.score}\n{opponent.name} score: {opponent.score}"

    return caption


async def main():
    roi_ref = get_refs()
    image_device = Path(settings.image_device)

    bot = await get_bot()
    task = asyncio.create_task(start_polling(bot))

    clean_dir(frames_path)
    clean_dir(regions_path)
    clean_dir(full_frames_path)

    try:
        while True:
            await game_loop(bot, image_device, roi_ref)
    finally:
        clean_dir(frames_path)
        clean_dir(regions_path)
        task.cancel()
        await task


def compile_video():
    timestamp = utcnow().strftime("%Y%m%d_%H%M%S")
    video_path = videos_path / f"game_{timestamp}.mp4"
    create_video(video_path, framerate=settings.fps)
    clean_dir(frames_path)
    return video_path


if __name__ == "__main__":
    asyncio.run(main())
