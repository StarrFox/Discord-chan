from dataclasses import dataclass
from enum import Enum

import pendulum


class SnipeMode(Enum):
    edited = 1
    purged = 2
    deleted = 3


@dataclass
class Snipe:
    id: int
    mode: SnipeMode
    author: int
    content: str
    server: int
    channel: int
    time: pendulum.DateTime

    @property
    def discord_timestamp(self) -> str:
        return f"<t:{int(self.time.timestamp())}:R>"
