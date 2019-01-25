import discord
from discord.ext import commands
import asyncio

class owner:

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

def setup(bot):
    bot.add_cog(owner(bot))