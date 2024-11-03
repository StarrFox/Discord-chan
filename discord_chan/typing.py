from typing import TypeVar

import discord
from discord.ext import commands

BotT = TypeVar("BotT", bound=commands.Bot | commands.AutoShardedBot)

MessageableGuildChannel = discord.TextChannel | discord.Thread


# Message where guild is not None
class GuildMessage(discord.Message):
    guild: discord.Guild
    author: discord.Member  # type: ignore
    channel: MessageableGuildChannel  # type: ignore


# TODO: 3.12 GuildContext[T: commands.Bot](commands.Context[T])
# Context where guild is not None
class GuildContext(commands.Context[BotT]):
    guild: discord.Guild  # type: ignore
    author: discord.Member  # type: ignore
    channel: MessageableGuildChannel  # type: ignore
    me: discord.Member  # type: ignore
