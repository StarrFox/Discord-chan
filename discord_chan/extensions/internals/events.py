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
import datetime
from collections import Counter
from contextlib import suppress
from typing import Dict, List

import discord
from aiohttp import ClientSession as Session
from discord.ext import commands, tasks
from loguru import logger

from discord_chan import DiscordChan, Snipe, SnipeMode, db, utils


# Todo: add github cog using github api (replace copycat stuff)
# Todo: command usage tracking and statistics graphs


class Events(commands.Cog, name="events"):
    def __init__(self, bot: DiscordChan):
        self.bot = bot
        self.socket_events = Counter()
        self.command_uses = Counter()
        self.bot_prefixes: Dict[int, List[str]] = {}
        self.copycat = None
        self.tasks = []
        self.tasks.append(asyncio.create_task(self.update_anime_db()))
        self.tasks.append(asyncio.create_task(self.get_copycat()))
        self.tasks.append(asyncio.create_task(self.load_channel_links()))
        if self.bot.config.extra_tokens.top_gg:
            self.post_dbl_guilds.start()

    def cog_unload(self):
        for task in self.tasks:
            if not task.done():
                task.cancel()

        self.post_dbl_guilds.cancel()

    # Misc

    async def get_copycat(self):
        await self.bot.wait_until_ready()
        self.copycat = self.bot.get_channel(605115140278452373)

    @commands.Cog.listener("on_message")
    async def on_copycat(self, message: discord.Message):
        if self.copycat is None:
            return

        if message.channel.id in [381979045090426881, 381965829857738772]:
            await utils.msg_resend(self.copycat, message)

    @tasks.loop(hours=5)
    async def post_dbl_guilds(self):
        async with Session(raise_for_status=True) as sess:
            await sess.post(
                f"https://top.gg/api/bots/{self.bot.user.id}/stats",
                headers={"Authorization": self.bot.config.extra_tokens.top_gg},
                data={"server_count": len(self.bot.guilds)},
            )

            logger.debug("Posted DBL guild count.")

    @post_dbl_guilds.before_loop
    async def post_dbl_guild_before(self):
        await self.bot.wait_until_ready()

    @post_dbl_guilds.after_loop
    async def post_dbl_guild_after(self):
        if self.post_dbl_guilds.failed():
            logger.exception("DBL poster errored out, restarting")
            await asyncio.sleep(300)
            self.post_dbl_guilds.restart()

    # @commands.Cog.listener('on_message')
    # async def on_bot_message(self, message: discord.Message):
    #     """
    #     Listens for prefixes
    #     """
    #     if not message.author.bot:
    #         return
    #
    #     def get_message_before(m):
    #         return m.channel == message.channel and m.id < message.id
    #
    #     message_before = discord.utils.find(get_message_before, self.bot.cached_messages)

    # def get_prefix(self, bot_message: discord.Message, message_before: discord.Message):
    #     """
    #     Returns the prefix used to invoke this command
    #     :param bot_message:
    #     :param message_before:
    #     :return:
    #     """
    #     pass

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        self.bot.prefixes.pop(guild.id)
        async with db.get_database() as connection:
            await connection.execute(
                "DELETE FROM prefixes WHERE guild_id is ?;", (guild.id,)
            )
            await connection.commit()

    @commands.Cog.listener()
    async def on_socket_response(self, message):
        self.socket_events[message.get("t")] += 1

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        self.command_uses[ctx.command] += 1

    # Snipe

    def attempt_add_snipe(self, message: discord.Message, mode: str):
        try:
            mode = SnipeMode[mode]
        except KeyError:
            raise ValueError(f"{mode} is not a valid snipe mode.")
        if message.content:
            snipe = Snipe(message, mode)
            self.bot.snipes[message.guild.id][message.channel.id].appendleft(snipe)

    @commands.Cog.listener("on_message_delete")
    async def snipe_delete(self, message: discord.Message):
        self.attempt_add_snipe(message, "deleted")

    @commands.Cog.listener("on_bulk_message_delete")
    async def bulk_snipe_delete(self, messages: [discord.Message]):
        for message in messages:
            self.attempt_add_snipe(message, "purged")

    @commands.Cog.listener("on_message_edit")
    async def snipe_edit(self, before: discord.Message, after: discord.Message):
        if before.content != after.content:
            self.attempt_add_snipe(before, "edited")

    # Anime

    async def update_anime_db(self):
        """
        Updates anime_db with fresh info
        """
        with suppress(asyncio.CancelledError):
            self.bot.anime_db = await self.bot.jikan.schedule()

            now = datetime.datetime.utcnow()
            next_monday = datetime.timedelta(days=(7 - now.weekday()))

            await asyncio.sleep(next_monday.total_seconds())

    # Channel linking

    async def load_channel_links(self):
        """
        Loads channel links into memory as TextChannels
        """
        async with db.get_database() as connection:
            cursor = await connection.execute("SELECT * FROM channel_links;")
            for send_from, send_to in await cursor.fetchall():
                send_from_channel = self.bot.get_channel(send_from)
                if not send_from_channel:
                    logger.info(f"{send_from} is no longer accessable.")
                    continue

                channels = set()
                for channel_id in send_to:
                    channel = self.bot.get_channel(int(channel_id))
                    if channel:
                        channels.add(channel)
                    else:
                        logger.info(
                            f"{channel_id} is no longer accessable. (linked to {send_from_channel.name})"
                        )

                self.bot.channel_links[send_from_channel] = channels

    @commands.Cog.listener("on_message")
    async def on_linked_message(self, message: discord.Message):
        """
        Handles the actual "linking" of channels
        """
        # Don't send messages with only files
        if not message.content and not message.embeds:
            return

        # send_from -> send_to
        if message.channel in self.bot.channel_links and not message.author.bot:
            for channel in self.bot.channel_links[message.channel]:
                await channel.send(content=message.content)

        # send_to -> send_from
        elif (
            message.channel in [i for s in self.bot.channel_links.values() for i in s]
            and message.author != self.bot.user
        ):
            for send_from in self.bot.channel_links:
                if message.channel in self.bot.channel_links[send_from]:
                    webhook = discord.utils.get(
                        await send_from.webhooks(), name="channel_link"
                    )
                    if webhook is None:
                        webhook = await send_from.create_webhook(name="channel_link")

                    if len(message.author.display_name) < 20:
                        name = message.author.display_name + f" [{message.author.id}]"
                    else:
                        name = message.author.display_name

                    await webhook.send(
                        content=message.clean_content if message.content else None,
                        embeds=message.embeds,
                        username=name,
                        avatar_url=str(message.author.avatar_url_as(format="png")),
                    )


def setup(bot):
    bot.add_cog(Events(bot))
