import json
import discord
import asyncio
import logging
import traceback

from extras import utils
from collections import Counter
from discord.ext import commands

logger = logging.getLogger(__name__)

class events(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.copycat = self.bot.get_channel(605115140278452373)
        self.socket_events = Counter()

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handles incoming messages"""
        if not self.copycat:
            return
        if message.channel.id in [381979045090426881, 381965829857738772]:
            await utils.msg_resend(message, self.copycat)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.bot.prefixes[guild.id] = ['dc!']
        logger.info(f"Joined {guild.name}")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        self.bot.prefixes.pop(guild.id)
        logger.info(f"Left {guild.name}")

    @commands.Cog.listener()
    async def on_socket_response(self, message):
        self.socket_events[message.get('t')] += 1

def setup(bot):
    bot.add_cog(events(bot))
