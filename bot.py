from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile

from config import settings


def get_bot() -> Bot:
    return Bot(token=settings.bot_token)


async def send_video_to_telegram(bot: Bot, video_path: Path, caption: str):
    await bot.send_video(
        chat_id=settings.bot_channel,
        video=FSInputFile(video_path),
        caption=caption,
    )
