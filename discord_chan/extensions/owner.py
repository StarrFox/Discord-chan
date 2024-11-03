from io import BytesIO
import typing

import aiohttp
import discord
from discord.ext import commands

from discord_chan import DiscordChan, SubContext
import discord_chan
from discord_chan.converters import EnumConverter


class Owner(commands.Cog, name="owner"):
    """
    Owner commands
    """

    def __init__(self, bot: DiscordChan):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:  # type: ignore (this method is allowed to be sync and async)
        if not await self.bot.is_owner(ctx.author):
            raise commands.NotOwner("You do not own this bot")
        return True

    @commands.group(name="dbg")
    async def debug_command(self, ctx: SubContext):
        """
        various debug commands
        """
        return

    @debug_command.command()
    async def error(self, ctx: SubContext):
        raise Exception("test error")

    @debug_command.command()
    async def enable(self, ctx: SubContext, *, cmd):
        command = self.bot.get_command(cmd)

        if command is None:
            return await ctx.send("Command not found")

        command.enabled = True
        await ctx.confirm("Command enabled")

    @debug_command.command()
    async def disable(self, ctx: SubContext, *, cmd):
        command = self.bot.get_command(cmd)

        if command is None:
            return await ctx.send("Command not found")

        command.enabled = False
        await ctx.confirm("Command disabled")

    @debug_command.command()
    async def resend_file(self, ctx: SubContext, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.read()

        try:
            filename = url.split("/")[-1]
        except IndexError:
            filename = None

        await ctx.send(file=discord.File(BytesIO(data), filename))

    @debug_command.command()
    async def purge_feature(
        self, 
        ctx: SubContext, 
        feature: typing.Annotated[discord_chan.Feature, EnumConverter(discord_chan.Feature)]
    ):
        await self.bot.feature_manager.purge_feature(feature)
        await ctx.confirm("Feature purged")


async def setup(bot):
    await bot.add_cog(Owner(bot))
