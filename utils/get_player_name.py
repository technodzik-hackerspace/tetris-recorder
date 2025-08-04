from aiogram.types import User


def get_user_name(user: User) -> str:
    if user.username:
        return f"@{user.username}"
    if user.first_name:
        return user.first_name
    if user.last_name:
        return f"#{user.id}"
