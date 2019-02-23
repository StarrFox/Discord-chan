import discord
from discord.ext import commands
import asyncio
from os import system
import typing

class owner(commands.Cog):
    """Owner commands"""

    def __init__(self, bot):
        self.bot = bot
        self.dbl_state = False

    @commands.command()
    @commands.is_owner()
    async def dm(self, ctx, user: discord.User, *, msg: str):
        await user.send(msg)
        await ctx.send("message sent")

    @commands.command(aliases=["restart"])
    @commands.is_owner()
    async def shutdown(self, ctx):
        await ctx.send("😡")
        await self.bot.logout()

    @commands.command()
    @commands.is_owner()
    async def dbl(self, ctx, toggle: typing.Optional[bool] = None, time: int = 1800):
        if toggle is None:
            if self.dbl_state:
                return await ctx.send("Dbl update tasks are ON.")
            return await ctx.send("Dbl update tasks are OFF.")
        cog = self.bot.get_cog('events')
        if toggle is True:
            if self.dbl_state:
                return await ctx.send("Dbl tasks already started")
            await cog.start_dbl(time)
            self.dbl_state = True
            return await ctx.send("Started Dbl tasks")
        if toggle is False:
            if not self.dbl_state:
                return await ctx.send("Dbl tasks are not running")
            await cog.stop_dbl()
            self.dbl_state = False
            return await ctx.send("Stopped Dbl tasks")

def setup(bot):
    bot.add_cog(owner(bot))