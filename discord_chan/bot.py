import pathlib
import typing
from datetime import datetime
from collections.abc import Iterable

import discord
from discord.ext import commands
from loguru import logger
from aexaroton import Client as AexarotonClient

from .context import SubContext
from .database import Database
from .features import FeatureManager
from .help import Minimal

DEFAULT_PREFIXES = ["sf/", "SF/", "dc/", "DC/"]
ROOT = pathlib.Path(__file__).parent


class DiscordChan(commands.AutoShardedBot):
    def __init__(self, *, database: Database, exaroton_client: AexarotonClient, debug_mode: bool = False):
        super().__init__(
            command_prefix=self.get_command_prefix,
            case_insensitive=True,
            max_messages=10_000,
            help_command=Minimal(),
            allowed_mentions=discord.AllowedMentions.none(),
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"{DEFAULT_PREFIXES[0]}help",
            ),
            intents=discord.Intents.all(),
        )
        self.debug_mode: bool = debug_mode
        self.exaroton_client = exaroton_client
        self.database = database
        self.context = SubContext
        self.ready_once = False
        self.uptime = datetime.now()
        self.feature_manager = FeatureManager(self.database)

        self._owners_cache: int | list[int] | None = None

        self.add_check(self.direct_message_check)

    @classmethod
    async def create(cls, *, exaroton_token: str, debug_mode: bool = False):
        database: Database = await Database.create(debug_mode=debug_mode)
        exaroton_client = AexarotonClient(exaroton_token)
        return cls(database=database, exaroton_client=exaroton_client)

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
    async def owners(self, as_users: typing.Literal[False]) -> Iterable[int]: ...

    @typing.overload
    async def owners(
        self, as_users: typing.Literal[True]
    ) -> Iterable[discord.User]: ...

    @typing.overload
    async def owners(self) -> Iterable[int]: ...

    async def owners(self, as_users: bool = False) -> Iterable[int | discord.User]:
        owners_or_owner = await self._get_owners()

        if isinstance(owners_or_owner, int):
            owners = [owners_or_owner]
        else:
            owners = owners_or_owner

        if as_users:
            # this should work even without intents
            return [self.get_user(id_) for id_ in owners]  # type: ignore

        return owners

    @staticmethod
    async def get_member_reference(ctx: SubContext, user_id: int) -> str:
        member = ctx.guild.get_member(user_id)

        if member is None:
            try:
                user = await ctx.bot.fetch_user(user_id)
            except discord.NotFound:
                # deleted account
                user_name = str(user_id)
            else:
                user_name = user.display_name
        else:
            user_name = member.mention

        return user_name

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

        try:
            await self.load_extension("jishaku")
        except (commands.errors.ExtensionError, commands.errors.ExtensionFailed):
            logger.exception("Jishaku failed to load")

        try:
            await self.load_extension("discord_chan.emote_manager.emote_manager")
        except (commands.errors.ExtensionError, commands.errors.ExtensionFailed):
            logger.exception("Emote manager failed to load")

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

        extension_names: list[str] = []

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

    async def get_command_prefix(self, _: typing.Self, message: discord.Message):
        prefixes = DEFAULT_PREFIXES

        if self.debug_mode:
            prefixes = ["dg/"]

        return commands.when_mentioned_or(*prefixes)(self, message)

    @staticmethod
    def direct_message_check(ctx: SubContext):
        if isinstance(ctx.channel, discord.DMChannel):
            raise commands.NoPrivateMessage()

        return True
