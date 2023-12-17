import pathlib
import typing
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
                discord.AllowedMentions.none(),
            ),
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"{DEFAULT_PREFIXES[0]}help",
            ),
            intents=kwargs.pop("intents", discord.Intents.all()),
            # NOTE: remove if a team starts being used
            # this is to fix discord.py not using Optional correctly
            # see: https://github.com/Rapptz/discord.py/pull/9687
            owner_ids=kwargs.pop("owner_ids", None),
            **kwargs,
        )
        self.context = context
        self.ready_once = False
        self.uptime = datetime.now()
        self.database = Database()
        self.feature_manager = FeatureManager(self.database)

        self._owners_cache: int | list[int] | None = None

        self.add_check(self.direct_message_check)

    async def _get_owners(self) -> int | list[int]:
        if self._owners_cache is not None:
            return self._owners_cache

        application_info = await self.application_info()

        if application_info.team:
            self._owners_cache = [m.id for m in application_info.team.members]
        else:
            self._owners_cache = application_info.owner.id

        return self._owners_cache

    async def owners_mention(self) -> str:
        owners = await self.owners(as_users=True)
        return " ".join(o.mention for o in owners)

    @typing.overload
    async def owners(self, as_users: typing.Literal[False]) -> typing.Iterable[int]:
        ...

    @typing.overload
    async def owners(
        self, as_users: typing.Literal[True]
    ) -> typing.Iterable[discord.User]:
        ...

    @typing.overload
    async def owners(self) -> typing.Iterable[int]:
        ...

    async def owners(self, as_users: bool = False) -> typing.Iterable:
        owners_or_owner = await self._get_owners()

        if isinstance(owners_or_owner, int):
            owners = [owners_or_owner]
        else:
            owners = owners_or_owner

        if as_users:
            # this should work even without intents
            return [self.get_user(id_) for id_ in owners]

        return owners

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

        logger.info(f"Logged in as {self.user}")
        logger.info(f"Bot ready with {len(self.extensions.keys())} extensions")

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
            prefixes = ["dg/"]

        return commands.when_mentioned_or(*prefixes)(self, message)

    @staticmethod
    def direct_message_check(ctx: commands.Context):
        if isinstance(ctx.channel, discord.DMChannel):
            raise commands.NoPrivateMessage()

        return True
