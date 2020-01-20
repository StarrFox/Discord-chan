# -*- coding: utf-8 -*-
#  Copyright © 2019 StarrFox
#
#  Discord Chan is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Discord Chan is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with Discord Chan.  If not, see <https://www.gnu.org/licenses/>.

import asyncio
import logging
from collections import Counter

import discord
from discord.ext import commands

from discord_chan import utils

logger = logging.getLogger(__name__)

# Todo: add audit log dispatcher; dispatch audit_log_action
# Todo: add github cog using github api (replace copycat stuff)
# Todo: command usage tracking and statistics graphs (socket stats also?)

class Events(commands.Cog, name='events'):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.socket_events = Counter()
        self.copycat = None
        asyncio.create_task(self.get_copycat())

    async def get_copycat(self):
        await self.bot.wait_until_ready()
        self.copycat = self.bot.get_channel(605115140278452373)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handles incoming messages"""
        if self.copycat is None:
            return

        if message.channel.id in [381979045090426881, 381965829857738772]:
            await utils.msg_resend(self.copycat, message)

    # Todo: add db quarry
    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        self.bot.prefixes.pop(guild.id)

    @commands.Cog.listener()
    async def on_socket_response(self, message: discord.Message):
        self.socket_events[message.get('t')] += 1

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """
        Dispatches on_member_kick and on_member_ban
        """

def setup(bot):
    bot.add_cog(Events(bot))
