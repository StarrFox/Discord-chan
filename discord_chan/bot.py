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

import pathlib
from collections import defaultdict, deque
from datetime import datetime
from typing import Optional, Dict, Union, Deque, Set

import discord
from aioec import Client as EcClient
from box import ConfigBox
from discord.ext import commands
from jikanpy import AioJikan
from loguru import logger

from . import db, utils
from .context import SubContext
from .errors import AuthorBlacklisted
from .help import Minimal
from .snipe import Snipe


class DiscordChan(commands.AutoShardedBot):
    def __init__(
        self, config: ConfigBox, *, context: commands.Context = SubContext, **kwargs
    ):
        """
        :param config: Config parser object
        :param context: Context factory to use
        """
        super().__init__(
            command_prefix=kwargs.pop("command_prefix", self.get_command_prefix),
            case_insensitive=kwargs.pop("case_insensitive", True),
            max_messages=kwargs.pop("max_messages", 10_000),
            help_command=kwargs.pop("help_command", Minimal()),
            allowed_mentions=kwargs.pop(
                "allowed_mentions", discord.AllowedMentions(everyone=False, roles=False)
            ),
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"{config.general.prefix}help",
            ),
            **kwargs,
        )
        self.config = config
        self.context = context
        self.jikan = AioJikan()
        self.ready_once = False
        self.uptime = datetime.now()
        # Todo: make an anime entry object to replace the dicts in the lists
        self.anime_db: Dict[str, list] = {}
        # {user_id: reason}
        self.blacklist: Dict[int, Optional[str]] = {}
        self.past_invokes = utils.LRU(maxsize=1000)
        # {bot_id: {prefixes}}
        self.other_bot_prefixes: Dict[int, Set[str]] = defaultdict(lambda: set())
        # {guild_id: {prefixes}}
        self.prefixes: Dict[int, Set[str]] = defaultdict(
            lambda: {config.general.prefix}
        )
        # {send_from: {send_to}}
        self.channel_links: Dict[
            discord.TextChannel, Set[discord.TextChannel]
        ] = defaultdict(lambda: set())
        # {guild_id: {channel_id: deque[Snipe]}}
        self.snipes: Dict[int, Dict[int, Deque[Snipe]]] = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=5_000))
        )

        if config.extra_tokens.emote_collector:
            self.ec = EcClient(token=config.extra_tokens.emote_collector)

        else:
            self.ec = None

        self.add_check(self.blacklist_check)

    def get_message(self, message_id: int) -> Optional[discord.Message]:
        """
        Gets a message from cache
        :param message_id: The message id to get
        """
        return discord.utils.get(self.cached_messages, id=message_id)

    async def process_commands(self, message):
        if message.author.bot:
            return

        ctx = await self.get_context(message, cls=self.context)

        await self.invoke(ctx)

    async def on_message_edit(self, before, after):
        if before.content != after.content:
            await self.process_commands(after)

    async def on_ready(self):
        if self.ready_once:
            return

        self.ready_once = True

        await self.load_prefixes()

        if self.config.general.bool("load_extensions"):
            self.load_extensions_from_dir("discord_chan/extensions")

        logger.info(f"Bot ready with {len(self.extensions.keys())} extensions.")

    def run(self, *args, **kwargs):
        return super().run(self.config.discord.token, *args, **kwargs)

    def load_extensions_from_dir(self, path: Union[str, pathlib.Path]) -> int:
        """
        Loads any python files in a directory and it's children
        as extensions

        :param path: Path to directory to load
        :return: Number of extensions loaded
        """
        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path)

        if not path.is_dir():
            return 0

        before = len(self.extensions.keys())

        extension_names = []

        for subpath in path.glob("**/[!_]*.py"):  # Ignore if starts with _

            parts = subpath.with_suffix("").parts
            if parts[0] == ".":
                parts = parts[1:]

            extension_names.append(".".join(parts))

        for ext in extension_names:
            try:
                self.load_extension(ext)
            except (commands.errors.ExtensionError, commands.errors.ExtensionFailed):
                logger.exception("Failed loading " + ext)

        return len(self.extensions.keys()) - before

    async def get_command_prefix(self, _, message: discord.Message):
        if message.guild:
            # sorting fixes cases where part of another prefix is a prefix for example
            # if the prefix d was before dc/, c/ would be interpreted as a command
            prefixes = sorted(
                self.prefixes[message.guild.id], key=lambda s: len(s), reverse=True
            )

            return commands.when_mentioned_or(*prefixes)(self, message)
        else:  # DM
            return commands.when_mentioned_or(self.config.general.prefix, "")(
                self, message
            )

    def blacklist_check(self, ctx: commands.Context):
        if ctx.author.id in self.blacklist:
            reason = self.blacklist[ctx.author.id]
            raise AuthorBlacklisted(f"{ctx.author} is blacklisted for {reason}.")

        return True

    async def load_prefixes(self):
        async with db.get_database() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("SELECT * FROM prefixes;")
                for guild_id, prefixes in await cursor.fetchall():
                    self.prefixes[guild_id] = prefixes

        logger.info(f"Loaded prefixes for {len(self.prefixes)} guilds.")

    # This doesnt actually get called anymore
    async def unload_prefixes(self):
        async with db.get_database() as connection:
            async with connection.cursor() as cursor:
                await cursor.executemany(
                    "INSERT INTO prefixes (guild_id, prefixes) VALUES (?, ?) "
                    "ON CONFLICT (guild_id) DO UPDATE SET prefixes = EXCLUDED.prefixes",
                    self.prefixes.items(),
                )
            await connection.commit()

        logger.info(f"Unloaded prefixes for {len(self.prefixes)} guilds.")

    async def load_blacklist(self):
        async with db.get_database() as connection:
            cursor = await connection.execute("SELECT * FROM blacklist;")
            for user_id, reason in await cursor.fetchall():
                self.blacklist[user_id] = reason

        logger.info(f"Loaded {len(self.blacklist)} blacklisted users.")
