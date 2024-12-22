from aiogram.types import User


class PlayerCommitment:
    p1: User | None = None
    p2: User | None = None
    _started: bool = False

    def apply(self, player: str, user: User):
        if self._started:
            raise ValueError("Game already started")
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
        self._started = False

    def start(self):
        self._started = True

    @property
    def p1_name(self):
        if not self.p1:
            return "P1"
        return self.get_player_name(self.p1)

    @property
    def p2_name(self):
        if not self.p2:
            return "P2"
        return self.get_player_name(self.p2)

    @staticmethod
    def get_player_name(player: User):
        if player.username:
            return f"@{player.username}"
        if player.first_name:
            return player.first_name
        if player.last_name:
            return f"#{player.id}"


player_commitment = PlayerCommitment()
