import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import BotCommand, FSInputFile, Message, Update

from commitment import player_commitment
from config import settings
from utils.get_player_name import get_user_name


async def send_video_to_telegram(bot: Bot, chat_id, video_path: Path, caption: str):
    await bot.send_video(
        chat_id=chat_id,
        video=FSInputFile(video_path),
        caption=caption,
    )


async def get_bot():
    bot = Bot(token=settings.bot_token)

    await bot.set_my_commands(
        [
            BotCommand(
                command="p1",
                description="Apply as player 1",
            ),
            BotCommand(
                command="p2",
                description="Apply as player 2",
            ),
        ]
    )

    return bot


class LogDispatcher(Dispatcher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = logging.getLogger("dispatcher")
        self.log.setLevel(logging.INFO)
        self.log.addHandler(logging.StreamHandler())

    async def feed_update(self, bot: Bot, update: Update, **kwargs):
        msg = update.message

        if msg:
            from_user = msg.from_user
            self.log.info(f"msg: {from_user.username or from_user.id} -> {msg.text!r}")

        callback = update.callback_query
        if callback:
            from_user = callback.from_user
            self.log.info(
                f"callback: {from_user.username or from_user.id} -> {callback.data!r}"
            )

        return await super().feed_update(bot, update, **kwargs)


async def start_polling(bot: Bot):
    dp = LogDispatcher()

    @dp.message(Command("p1", "p2"))
    async def command_start_handler(message: Message) -> None:
        try:
            result = player_commitment.apply(message.text[1:], message.from_user)
        except ValueError as e:
            await message.answer(str(e))
            return

        if not result:
            return

        await message.answer(
            f"{get_user_name(message.from_user)} applied as {message.text[1:].upper()}!"
        )

    await dp.start_polling(bot)
