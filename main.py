import argparse
import asyncio
import logging
from asyncio import sleep
from copy import deepcopy
from datetime import datetime, UTC
from pathlib import Path

from aiogram import Bot

from bot import get_bot, send_video_to_telegram
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


async def game_loop(bot: Bot | None, image_device: Path, roi_ref: RoiRef):
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

        # Log state every 100 frames
        if frame_number % 100 == 0:
            log.info(f"Frame {frame_number}, input shape: {frame.shape}")

        try:
            f = Frame.strip(frame)
        except Exception as e:
            if frame_number % 100 == 0:
                log.warning(f"Frame.strip failed: {e}, input shape: {frame.shape}")
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
            if frame_number % 100 == 0:
                log.info("Game not detected")
            continue

        if frame_number % 100 == 0:
            log.info("Game detected, recording frame")

        save_image(frames_path / f"{frame_number:06d}.png", frame)

        try:
            screens = f.get_player_screens(roi_ref)
        except Exception as e:
            # Can't detect player screens (e.g., main menu "push start button" screen)
            log.debug(f"Could not detect player screens: {e}")
            continue

        if not game_started:
            try:
                score1 = screens[0].score_frame.score
                score2 = screens[1].score_frame.score
            except Exception:
                clean_dir(frames_path)
                continue

            if score1 == 0 and score2 == 0:
                log.info("Start: 2 player game")
                players = [Player("P1"), Player("P2")]
                game_started = True
                midgame = True
            else:
                if midgame is False:
                    midgame = True
                    log.info("Midgame, waiting for start")
                clean_dir(frames_path)
                continue
        else:
            midgame = False

        for p, screen in zip(players, screens):
            p.parse_frame(screen)

        if players[0].score is None:
            break

        # Detect new game start (scores reset to 0-0) during an active game
        if (
            game_started
            and all(p.score == 0 for p in players)
            and any(s is not None and s > 0 for s in last_score)
        ):
            log.info(f"New game detected (scores reset). Final score was: {last_score}")
            video_path = compile_video()
            log.info(f"Video created: {video_path}")

            if bot:
                caption = f"🎮 Game Over!\nP1: {last_score[0]} | P2: {last_score[1]}"
                await send_video_to_telegram(bot, video_path, caption)
                log.info(f"Video sent to channel {settings.bot_channel}")
            break

        if last_score != [i.score for i in players]:
            last_score = [i.score for i in players]
            log.info(f"Score: {last_score}")

        if last_game_over != [i.game_over for i in players]:
            for go, p in zip(last_game_over, players):
                if go != p.game_over:
                    log.info(f"{p.name} game over: {p.score}")
            last_game_over = [i.game_over for i in players]

        if all(i.game_over for i in players) and game_started:
            log.info(f"Final score: {last_score}")

            video_path = compile_video()
            log.info(f"Video created: {video_path}")

            if bot:
                caption = f"Game Over!\nP1: {players[0].score} | P2: {players[1].score}"
                await send_video_to_telegram(bot, video_path, caption)
                log.info(f"Video sent to channel {settings.bot_channel}")
            break

        # 10 fps
        spent_time = utcnow() - frame_start
        await sleep(max(0.0, (1 / settings.fps) - spent_time.total_seconds()))

    # Pause for a moment before starting a new recording
    await sleep(1)


async def main():
    logging.basicConfig(level=logging.INFO)
    roi_ref = get_refs()

    debug_mode = getattr(settings, "debug", False)
    no_bot = getattr(settings, "no_bot", False)

    # Debug mode: use video file instead of capture device
    if debug_mode:
        image_device = Path(settings.debug_video)
        logging.info(f"Debug mode: using video file {image_device}")
    else:
        image_device = Path(settings.image_device)

    # Initialize bot unless --no-bot is specified
    bot = None
    if not no_bot:
        bot = get_bot()
    else:
        logging.info("Running without Telegram bot")

    clean_dir(frames_path)
    clean_dir(regions_path)
    clean_dir(full_frames_path)

    try:
        while True:
            await game_loop(bot, image_device, roi_ref)
            if debug_mode:
                logging.info("Debug mode: exiting after processing video")
                break
    finally:
        clean_dir(frames_path)
        clean_dir(regions_path)


def compile_video():
    timestamp = utcnow().strftime("%Y%m%d_%H%M%S")
    video_path = videos_path / f"game_{timestamp}.mp4"
    create_video(video_path, frames_path=frames_path / "*.png", framerate=settings.fps)
    clean_dir(frames_path)
    return video_path


def parse_args():
    parser = argparse.ArgumentParser(description="Tetris Recorder")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run in debug mode using gameplay_example.mp4 as input",
    )
    parser.add_argument(
        "--video",
        type=str,
        help="Path to video file (implies --debug)",
    )
    parser.add_argument(
        "--no-bot",
        action="store_true",
        help="Skip Telegram bot integration (useful for testing)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.debug or args.video:
        settings.debug = True
        if args.video:
            settings.debug_video = args.video
    if args.no_bot:
        settings.no_bot = True
    asyncio.run(main())
