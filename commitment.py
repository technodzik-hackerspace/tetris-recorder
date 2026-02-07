from aiogram.types import User

from utils.get_player_name import get_user_name


class PlayerCommitment:
    p1: User | None = None
    p2: User | None = None

    def apply(self, player: str, user: User):
        if player not in ("p1", "p2"):
            raise ValueError("Invalid player")
        if user in (self.p1, self.p2):
            raise ValueError("You already applied")

        if player == "p1":
            self.p1 = user
            return True
        elif player == "p2":
            self.p2 = user
            return True

    def clear(self):
        self.p1 = None
        self.p2 = None

    @property
    def p1_name(self):
        if not self.p1:
            return "P1"
        return get_user_name(self.p1)

    @property
    def p2_name(self):
        if not self.p2:
            return "P2"
        return get_user_name(self.p2)


player_commitment = PlayerCommitment()
