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

import logging
from collections import Counter

import discord
from bot_stuff import DiscordHandler
from discord.ext import commands

import config
from extras import utils

logger = logging.getLogger(__name__)
logger.propagate = False

if not logger.handlers:
    logger.addHandler(
        DiscordHandler(
            config.webhook_url,
            logging.INFO
        )
    )

class events(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.copycat = self.bot.get_channel(605115140278452373)
        self.socket_events = Counter()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handles incoming messages"""
        if not self.copycat:
            return
        if message.channel.id in [381979045090426881, 381965829857738772]:
            await utils.msg_resend(message, self.copycat)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self.bot.prefixes[guild.id] = [config.prefix]

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        self.bot.prefixes.pop(guild.id)

    @commands.Cog.listener()
    async def on_socket_response(self, message: discord.Message):
        self.socket_events[message.get('t')] += 1

def setup(bot):
    bot.add_cog(events(bot))
