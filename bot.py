from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile

from config import settings

bot = Bot(token=settings.bot_token)


async def send_video_to_telegram(video_path: Path, caption: str):
    await bot.send_video(
        chat_id=settings.chat_id,
        video=FSInputFile(video_path),
        caption=caption,
    )
