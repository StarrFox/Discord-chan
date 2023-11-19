from typing import TYPE_CHECKING

from discord.ext import commands

if TYPE_CHECKING:
    from discord_chan import Feature, DiscordChan

class CogNotLoaded(commands.CheckFailure):
    def __init__(self, cog_name: str):
        super().__init__(f"{cog_name} is not loaded.")


def cog_loaded(cog_name: str):
    def _pred(ctx):
        if ctx.bot.get_cog(cog_name):
            return True

        raise CogNotLoaded(cog_name)

    return commands.check(_pred)


def some_guilds(*guilds: int):
    def _pred(ctx):
        return ctx.guild.id in guilds

    return commands.check(_pred)


def guild_owner():
    def _pred(ctx: commands.Context):
        if ctx.guild is None:
            return False

        return ctx.author.id == ctx.guild.owner_id

    return commands.check(_pred)


def feature_enabled(feature: "Feature"):
    async def _pred(ctx: commands.Context["DiscordChan"]):
        if ctx.guild is None:
            return False

        return await ctx.bot.feature_manager.is_enabled(feature, ctx.guild.id)

    return commands.check(_pred)
