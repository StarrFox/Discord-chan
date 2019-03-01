import discord
from discord.ext import commands
import asyncio
from os import system
import typing
from tabulate import tabulate
import traceback

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

#Modified from
#https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/admin.py#L209-L250

    @commands.command()
    @commands.is_owner()
    async def sql(self, ctx, *, entry: str):
        """Sql command"""
        is_multistatement = entry.count(';') > 1
        if is_multistatement:
            strategy = self.bot.db.execute
        else:
            strategy = self.bot.db.fetch
        try:
            results = await strategy(entry)
        except Exception:
            return await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        rows = len(results)
        if is_multistatement or rows == 0:
            return await ctx.send(f'`{results}`')
        tube = []
        header = list(results[0].keys())
        tube.append(list(i.values()) for i in results)
        tab = tabulate(tube, header, tablefmt='fancy_grid')
        await ctx.send(f"```py\n{tab}```")

def setup(bot):
    bot.add_cog(owner(bot))
