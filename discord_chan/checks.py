from typing import TYPE_CHECKING

from discord.ext import commands

if TYPE_CHECKING:
    from discord_chan import DiscordChan, Feature


def cog_loaded(cog_name: str):
    def _pred(ctx):
        if ctx.bot.get_cog(cog_name):
            return True

        raise commands.CheckFailure(f"{cog_name} is not loaded")

    return commands.check(_pred)


def some_guilds(*guilds: int):
    def _pred(ctx: commands.Context):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()

        if not ctx.guild.id in guilds:
            raise commands.CheckFailure("Guild not in allowed list")

        return True

    return commands.check(_pred)


def guild_owner():
    def _pred(ctx: commands.Context):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()

        if not ctx.author.id == ctx.guild.owner_id:
            raise commands.CheckFailure("You must be the server owner to run this command")

        return True

    return commands.check(_pred)


def feature_enabled(feature: "Feature"):
    async def _pred(ctx: commands.Context["DiscordChan"]):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()

        if not await ctx.bot.feature_manager.is_enabled(feature, ctx.guild.id):
            raise commands.CheckFailure(f"Feature \"{feature.name}\" must be enabled to use this command")

        return True

    return commands.check(_pred)
