# -*- coding: utf-8 -*-
#  Copyright © 2020 StarrFox
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

import discord
from discord.ext import commands
from loguru import logger

from discord_chan import PartitionPaginator


class Logging(commands.Cog, name='logging'):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.handler_id = logger.add(
            self.send_to_webhook,
            format='{level.icon} [{level}] ({time:YYYY-MM-DD HH:mm:ss.SSS}) -'
                   '` {name}:{function}:{line}` - {message}',
            level='INFO'
        )

    async def send_to_webhook(self, message):
        if self.bot.is_closed():
            return

        channel = self.bot.get_channel(int(self.bot.config['discord']['logging_channel']))

        if channel is None:
            # cache populating
            await asyncio.sleep(10)

            channel = self.bot.get_channel(int(self.bot.config['discord']['logging_channel']))

            if channel is None:
                raise RuntimeError('Config logging_channel id wrong.')

        webhook: discord.Webhook = discord.utils.get(await channel.webhooks(), name='Logging')

        if webhook is None:
            webhook = await channel.create_webhook(name='Logging')

        pager = PartitionPaginator(prefix=None, suffix=None)

        pager.add_line(message)

        # 30 = WARNING
        if message.record['level'].no >= 30:
            if self.bot.owner_id:
                pager.add_line(f'<@!{self.bot.owner_id}>')

            else:
                pager.add_line(' '.join([f'<@!{i}>' for i in self.bot.owner_ids]))

        if self.bot.owner_id:
            allowed_users = [discord.Object(id=self.bot.owner_id)]

        else:
            allowed_users = [discord.Object(id=i) for i in self.bot.owner_ids]

        for page in pager.pages:
            await webhook.send(
                page,
                username=str(message.record['module']),
                allowed_mentions=discord.AllowedMentions(
                    everyone=False,
                    roles=False,
                    users=allowed_users
                )
            )

    def cog_unload(self):
        logger.remove(self.handler_id)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild and message.author != self.bot.user:
            logger.info(
                f'DM author={message.author} ({message.author.id}) id={message.id} content={message.content}'
            )

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        percent_bots = round((sum(1 for i in guild.members if i.bot) / guild.member_count) * 100)

        logger.info(
            f'Joined_guild name={guild.name} id={guild.id} owner={guild.owner} ({guild.owner.id})'
            f' percent_bots={percent_bots}'
        )

def setup(bot: commands.Bot):
    if bot.config['discord']['logging_channel']:
        bot.add_cog(Logging(bot))
