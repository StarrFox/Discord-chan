import discord
import asyncio
import json
import traceback
from discord.ext import commands
from extras import utils

class events(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.copycat = self.bot.get_channel(573606808384438292)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handles incoming messages"""
        if not self.copycat:
            return
        if message.channel.id == 381979045090426881:
            await utils.msg_resend(message, self.copycat)
        elif message.channel.id == 381965829857738772:
            await utils.msg_resend(message, self.copycat)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not after.embeds:
            await self.bot.process_commands(after)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.bot.prefixes[guild.id] = ['dc!']
        self.bot.logger.info(f"Joined {guild.name}")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        self.bot.prefixes.pop(guild.id)
        self.bot.logger.info(f"Left {guild.name}")

def setup(bot):
    bot.add_cog(events(bot))
