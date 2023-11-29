from dataclasses import dataclass
from enum import Enum

from discord.ext import commands
from pendulum.datetime import DateTime

from discord_chan.utils import to_discord_timestamp


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
    time: DateTime

    @property
    def discord_timestamp(self) -> str:
        return to_discord_timestamp(self.time)
