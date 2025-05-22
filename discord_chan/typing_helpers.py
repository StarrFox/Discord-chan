import discord
from discord.ext import commands

MessageableGuildChannel = discord.TextChannel | discord.Thread


# Message where guild is not None
class GuildMessage(discord.Message):
    guild: discord.Guild
    author: discord.Member  # type: ignore
    channel: MessageableGuildChannel  # type: ignore


# Context where guild is not None
class GuildContext[T: commands.Bot | commands.AutoShardedBot](commands.Context[T]):
    guild: discord.Guild  # type: ignore
    author: discord.Member  # type: ignore
    channel: MessageableGuildChannel  # type: ignore
    me: discord.Member  # type: ignore
