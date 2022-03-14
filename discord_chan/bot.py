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
from typing import Deque, Dict, Optional, Union, Type

import discord
from discord.ext import commands
from loguru import logger

from .context import SubContext
from .help import Minimal
from .snipe import Snipe


DEFAULT_PREFIXES = ["dc/", "DC/"]


class DiscordChan(commands.AutoShardedBot):
    def __init__(
        self, *, context: Type[commands.Context] = SubContext, **kwargs
    ):
        super().__init__(
            command_prefix=kwargs.pop("command_prefix", self.get_command_prefix),
            case_insensitive=kwargs.pop("case_insensitive", True),
            max_messages=kwargs.pop("max_messages", 10_000),
            help_command=kwargs.pop("help_command", Minimal()),
            allowed_mentions=kwargs.pop(
                "allowed_mentions",
                discord.AllowedMentions(everyone=False, roles=False, users=False),
            ),
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"dc/help",
            ),
            intents=kwargs.pop("intents", discord.Intents.all()),
            **kwargs,
        )
        self.context = context
        self.ready_once = False
        self.uptime = datetime.now()
        # {guild_id: {channel_id: deque[Snipe]}}
        self.snipes: Dict[int, Dict[int, Deque[Snipe]]] = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=5_000))
        )

        self.add_check(self.direct_message_check)

    def get_message(self, message_id: int) -> Optional[discord.Message]:
        """
        Gets a message from cache
        :param message_id: The message id to get
        """
        return discord.utils.get(self.cached_messages, id=message_id)

    async def process_commands(self, message: discord.Message):
        if message.author.bot:
            return

        ctx = await self.get_context(message, cls=self.context)

        await self.invoke(ctx)

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.content != after.content:
            if after.guild and not isinstance(after.author, discord.Member):
                # Cache bug, after.author is User while before.author is Member
                after.author = await after.guild.fetch_member(after.author.id)

            await self.process_commands(after)

    async def on_ready(self):
        if self.ready_once:
            return

        self.ready_once = True

        await self.load_extension("jishaku")
        await self.load_extensions_from_dir("extensions")

        logger.info(f"Logged in as {self.user}.")
        logger.info(f"Bot ready with {len(self.extensions.keys())} extensions.")

    async def load_extensions_from_dir(self, path: Union[str, pathlib.Path]) -> int:
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
                await self.load_extension(ext)
            except (commands.errors.ExtensionError, commands.errors.ExtensionFailed):
                logger.exception("Failed loading " + ext)

        return len(self.extensions.keys()) - before

    async def get_command_prefix(self, _, message: discord.Message):
        return commands.when_mentioned_or(*DEFAULT_PREFIXES)(self, message)

    @staticmethod
    def direct_message_check(ctx: commands.Context):
        if isinstance(ctx.channel, discord.DMChannel):
            raise commands.NoPrivateMessage()

        return True
