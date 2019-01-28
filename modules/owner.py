import discord
from discord.ext import commands
import asyncio
from os import system

class owner:
    """Owner commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def dm(self, ctx, user: discord.User, *, msg: str):
        await user.send(msg)
        await ctx.send("message sent")

    @commands.command()
    @commands.is_owner()
    async def shutdown(self, ctx):
        await ctx.send(":c")
        await self.bot.logout()

    @commands.command()
    @commands.is_owner()
    async def restart(self, ctx):
        await ctx.send('😡')
        system('start restart.py')
        await self.bot.logout()

def setup(bot):
    bot.add_cog(owner(bot))