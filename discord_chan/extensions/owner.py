from io import BytesIO

import aiohttp
import discord
from discord.ext import commands

from discord_chan import DiscordChan, SubContext


class Owner(commands.Cog, name="owner"):
    """
    Owner commands
    """

    def __init__(self, bot: DiscordChan):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context):
        if not await self.bot.is_owner(ctx.author):
            raise commands.NotOwner("You do not own this bot")
        return True

    @commands.command()
    async def enable(self, ctx: SubContext, *, cmd):
        command = self.bot.get_command(cmd)

        if command is None:
            return await ctx.send("Command not found.")

        command.enabled = True
        await ctx.confirm("Command enabled.")

    @commands.command()
    async def disable(self, ctx: SubContext, *, cmd):
        command = self.bot.get_command(cmd)

        if command is None:
            return await ctx.send("Command not found.")

        command.enabled = False
        await ctx.confirm("Command disabled.")

    @commands.command()
    async def resend_file(self, ctx: SubContext, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.read()

        try:
            filename = url.split("/")[-1]
        except IndexError:
            filename = None

        await ctx.send(file=discord.File(BytesIO(data), filename))


async def setup(bot):
    await bot.add_cog(Owner(bot))
