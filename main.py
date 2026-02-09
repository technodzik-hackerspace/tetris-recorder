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
from game_objects.frame_classifier import FrameClassifier
from game_objects.game_state import GameState, GameStateMachine
from utils.dirs import (
    cleanup_old_games,
    create_game_folder,
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
    _log.propagate = False

    return _log


async def game_loop(bot: Bot | None, image_device: Path, roi_ref: RoiRef):
    """Main game loop using FrameClassifier and GameStateMachine.

    Simplified flow:
    1. Classify each frame
    2. Skip paused frames
    3. Update state machine
    4. Record frames during GAME state (to timestamped folder)
    5. Handle game over (compile video, send to Telegram, cleanup old games)
    """
    _log = get_frame_logger("game")
    classifier = FrameClassifier(roi_ref)
    state_machine = GameStateMachine()

    pause_started = False
    last_score = [None, None]
    last_game_over = [False, False]
    game_folder: Path | None = None

    # FPS tracking
    fps_start_time = utcnow()
    fps_frame_count = 0

    for frame_number, raw_frame in enumerate(frame_generator(image_device)):
        await sleep(0)
        log = ILoggerAdapter(_log, {"frame_number": frame_number})
        fps_frame_count += 1

        # Log state every 100 frames with FPS and timing info
        if frame_number % 100 == 0:
            elapsed = (utcnow() - fps_start_time).total_seconds()
            fps = fps_frame_count / elapsed if elapsed > 0 else 0
            avg_timing = classifier.cumulative_timing.avg_str()
            log.info(
                f"Frame {frame_number}, FPS: {fps:.1f}, "
                f"state: {state_machine.state.name}, "
                f"avg timing: [{avg_timing}]"
            )
            # Reset counters for next interval
            fps_start_time = utcnow()
            fps_frame_count = 0
            classifier.cumulative_timing.reset()

        # 1. Classify frame
        # In debug mode during GAME state, skip score detection except every 100 frames
        # to improve performance. Always detect scores when game_over might be happening.
        debug_mode = getattr(settings, "debug", False)
        skip_score = (
            debug_mode
            and state_machine.state == GameState.GAME
            and frame_number % 100 != 0
            and not state_machine.game_over_detected
        )
        info = classifier.classify(raw_frame, skip_score=skip_score)

        # If game_over just detected and we skipped scores, re-classify to get final scores
        if info.both_game_over and skip_score:
            info = classifier.classify(raw_frame, skip_score=False)

        # 2. Skip paused frames (but NOT bonus frames - those should be recorded)
        if info.is_paused:
            if not pause_started:
                log.info("Pause")
                pause_started = True
            continue
        elif pause_started:
            log.info("Resume")
            pause_started = False

        # Log bonus frames (they will be recorded)
        if info.is_bonus:
            log.info("Bonus screen detected")

        # 3. Update state machine
        old_state, new_state = state_machine.update(info)

        # Log state transitions
        if old_state != new_state:
            log.info(f"State transition: {old_state.name} -> {new_state.name}")

        # Create game folder when game starts
        if old_state != GameState.GAME and new_state == GameState.GAME:
            game_folder = create_game_folder()
            log.info(f"Created game folder: {game_folder}")

        # Log when entering menu without recording
        if new_state == GameState.MENU:
            if frame_number % 100 == 0:
                log.info("In menu, waiting for game start")
            continue

        # Log when frame is not tetris
        if new_state == GameState.NOT_TETRIS:
            if frame_number % 100 == 0:
                log.info("Frame not detected as Tetris")
            continue

        # 4. Record frames only during GAME state
        if new_state == GameState.GAME and game_folder is not None:
            if frame_number % 100 == 0:
                log.info("Recording game frame")
            save_image(game_folder / f"{frame_number:06d}.png", raw_frame)

            # Log score changes (only when we have valid scores)
            if info.has_valid_scores:
                current_score = [info.p1_score, info.p2_score]
                if last_score != current_score:
                    last_score = current_score
                    log.info(f"Score: P1={info.p1_score} P2={info.p2_score}")

            # Log game over status changes
            current_game_over = [info.p1_game_over, info.p2_game_over]
            if last_game_over != current_game_over:
                if info.p1_game_over and not last_game_over[0]:
                    # Use state machine's score if current info doesn't have it
                    p1_score = info.p1_score if info.p1_score is not None else state_machine.last_p1_score
                    log.info(f"P1 game over: {p1_score}")
                if info.p2_game_over and not last_game_over[1]:
                    p2_score = info.p2_score if info.p2_score is not None else state_machine.last_p2_score
                    log.info(f"P2 game over: {p2_score}")
                if info.both_game_over and not all(last_game_over):
                    log.info("Both players game over, recording game over screen...")
                last_game_over = current_game_over

        # 5. Handle game over
        if new_state == GameState.GAME_OVER:
            if state_machine.video_ready and game_folder is not None:
                final_p1 = state_machine.final_p1_score
                final_p2 = state_machine.final_p2_score
                log.info(f"Game over! Final score: P1={final_p1} P2={final_p2}")

                video_path = compile_video(game_folder)
                log.info(f"Video created: {video_path}")

                # Cleanup old game folders, keep last 5
                removed = cleanup_old_games(keep_count=5)
                if removed:
                    log.info(f"Cleaned up {len(removed)} old game folder(s)")

                if bot:
                    caption = f"Game Over!\nP1: {final_p1} | P2: {final_p2}"
                    await send_video_to_telegram(bot, video_path, caption)
                    log.info(f"Video sent to channel {settings.bot_channel}")
            else:
                log.info("Game over detected but not a valid game (mid-game join)")

            state_machine.acknowledge_game_over()
            game_folder = None
            break

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

    while True:
        await game_loop(bot, image_device, roi_ref)
        if debug_mode:
            logging.info("Debug mode: exiting after processing video")
            break


def compile_video(game_folder: Path) -> Path:
    """Compile frames from a game folder into a video.

    Args:
        game_folder: Path to the game folder containing PNG frames

    Returns:
        Path to the created video file
    """
    videos_path.mkdir(exist_ok=True)
    # Use the game folder name for the video (already timestamped)
    video_name = f"{game_folder.name}.mp4"
    video_path = videos_path / video_name
    create_video(video_path, frames_path=game_folder / "*.png", framerate=settings.fps)
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
