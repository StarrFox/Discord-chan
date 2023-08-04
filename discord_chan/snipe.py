from dataclasses import dataclass
from enum import Enum

import pendulum
from discord.ext import commands


class SnipeMode(Enum):
    edited = 1
    purged = 2
    deleted = 3

    # this allows SnipeMode to be used as a command argument converter
    @classmethod
    async def convert(cls, _, argument: str):
        try:
            return cls[argument]
        except KeyError:
            raise commands.BadArgument(
                f"{argument} is not a valid snipe mode (edited/purged/deleted)"
            )


@dataclass
class Snipe:
    id: int
    mode: SnipeMode
    author: int
    content: str
    server: int
    channel: int
    # TODO: remove ignore in pendulum 3 (currently 2)
    time: pendulum.DateTime  # type: ignore

    @property
    def discord_timestamp(self) -> str:
        return f"<t:{int(self.time.timestamp())}:R>"
