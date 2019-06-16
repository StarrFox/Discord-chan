import discord
from discord.ext import commands

from os import system
import traceback
import typing
import asyncio
import json

from extras import utils

bool_dict = {
    "true": True,
    "on": True,
    "1": True,
    "false": False,
    "off": False,
    "0": False
}

jsk_settings = {
    "task": "<a:sonic:577005444191485952>",
    "done": "<a:dancin:582409853918511165>",
    "syntax": "<a:default:577017740016222229>",
    "timeout": "error:539157627385413633",
    "error": "<a:default:577017740016222229>",
    "tracebacks": "\N{BLACK DOWN-POINTING DOUBLE TRIANGLE}"
}

class owner(commands.Cog):
    """Owner commands"""

    def __init__(self, bot):
        self.bot = bot
        self.jsk_settings = {
            "task": "<a:sonic:577005444191485952>",
            "done": "<a:dancin:582409853918511165>",
            "syntax": "<a:default:577017740016222229>",
            "timeout": "error:539157627385413633",
            "error": "<a:default:577017740016222229>",
            "tracebacks": "\N{BLACK DOWN-POINTING DOUBLE TRIANGLE}",
            "retain": True
        }

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

    @commands.command()
    async def loadjsk(self, ctx):
        self.bot.load_extension('bot_stuff.jsk', **jsk_settings)
        await ctx.send('Loaded jsk')

    @commands.command()
    async def jskset(self, ctx, item: typing.Optional[str] = None, value: str = None):
        if item is None or value is None:
            return await ctx.send(utils.block(json.dumps(self.jsk_settings, indent=4)))
        if isinstance(self.jsk_settings[item], bool):
            self.jsk_settings[item] = bool_dict[value.lower()]
        else:
            self.jsksettings[item] = value
        await ctx.send("changed")

def setup(bot):
    bot.add_cog(owner(bot))
