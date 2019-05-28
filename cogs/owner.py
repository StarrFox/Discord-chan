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

    async def cog_check(self, ctx):
        if not await self.bot.is_owner(ctx.author):
            raise commands.NotOwner('You do not own this bot.')
        return True

    @commands.command()
    async def dm(self, ctx, user: discord.User, *, msg: str):
        await user.send(msg)
        await ctx.send("message sent")

    @commands.command(aliases=["restart"])
    async def shutdown(self, ctx):
        await ctx.send("😡")
        await self.bot.logout()

#Modified from
#https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/admin.py#L209-L250

    @commands.command()
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
        header = list(results[0].keys())
        tube = [list(i.values()) for i in results]
        tab = tabulate(tube, header, tablefmt='fancy_grid')
        await ctx.send(f"```py\n{tab}```")

    @commands.command()
    async def noprefix(self, ctx, toggle: bool = None):
        """Toogles having no prefix"""
        if toggle is None:
            if self.bot.noprefix:
                return await ctx.send("No prefix is currently on.")
            return await ctx.send("No prefix is currently off.")
        if toggle:
            if self.bot.noprefix:
                return await ctx.send("No prefix is already on.")
            self.bot.noprefix = True
            return await ctx.send("No prefix turned on.")
        if not self.bot.noprefix:
            return await ctx.send("No prefix is already off.")
        self.bot.noprefix = False
        return await ctx.send("No prefix turned off.")

    @commands.group(invoke_without_command=True)
    async def loadjsk(self, ctx):
        self.bot.load_extension('jishaku')
        await ctx.send('Loaded jsk')

    @loadjsk.command()
    async def sub(self, ctx):
        self.bot.load_extension('cogs.jsk')
        await ctx.send("Sub_jsk loaded")

    @commands.command()
    async def emoji(self, ctx, name, link):
        """Creates an emoji"""
        async with self.bot.session.get(link) as res:
            try:
                await ctx.guild.create_custom_emoji(name=name, image=await res.read())
                await ctx.check()
            except Exception as e:
                await ctx.send(e)

def setup(bot):
    bot.add_cog(owner(bot))
