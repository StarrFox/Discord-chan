import pathlib
from datetime import datetime

import discord
from discord.ext import commands
from loguru import logger

from .context import SubContext
from .database import Database
from .features import FeatureManager
from .help import Minimal

DEFAULT_PREFIXES = ["sf/", "SF/", "dc/", "DC/"]
ROOT = pathlib.Path(__file__).parent


class DiscordChan(commands.AutoShardedBot):
    def __init__(self, *, context: type[commands.Context] = SubContext, **kwargs):
        self.debug_mode: bool = kwargs.pop("debug_mode", False)
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
                name="sf/help",
            ),
            intents=kwargs.pop("intents", discord.Intents.all()),
            **kwargs,
        )
        self.context = context
        self.ready_once = False
        self.uptime = datetime.now()
        self.database = Database()
        self.feature_manager = FeatureManager(self.database)

        self.add_check(self.direct_message_check)

    def get_message(self, message_id: int) -> discord.Message | None:
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
        await self.load_extension("discord_chan.emote_manager.emote_manager")

        root = pathlib.Path(__file__).parent
        extensions_path = root / "extensions"
        await self.load_extensions_from_dir(extensions_path)

        logger.info(f"Logged in as {self.user}.")
        logger.info(f"Bot ready with {len(self.extensions.keys())} extensions.")

    async def load_extensions_from_dir(self, path: str | pathlib.Path) -> int:
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
            subpath = subpath.relative_to(ROOT)

            parts = subpath.with_suffix("").parts
            if parts[0] == ".":
                parts = parts[1:]

            extension_names.append(".".join(parts))

        for ext in extension_names:
            try:
                await self.load_extension("discord_chan." + ext)
            except (commands.errors.ExtensionError, commands.errors.ExtensionFailed):
                logger.exception("Failed loading " + ext)

        return len(self.extensions.keys()) - before

    async def get_command_prefix(self, _, message: discord.Message):
        prefixes = DEFAULT_PREFIXES

        if self.debug_mode:
            prefixes.append("dg/")

        return commands.when_mentioned_or(*prefixes)(self, message)

    @staticmethod
    def direct_message_check(ctx: commands.Context):
        if isinstance(ctx.channel, discord.DMChannel):
            raise commands.NoPrivateMessage()

        return True
