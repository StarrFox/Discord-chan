from io import BytesIO
import typing
import zipfile
from pathlib import Path
import tempfile
import asyncio
import uuid

import aiohttp
import discord
import yarl
from discord.ext import commands
from loguru import logger


import discord_chan
from discord_chan.typing import MessageableGuildChannel
from discord_chan import DiscordChan, SubContext
from discord_chan.converters import EnumConverter
from discord_chan.image import get_bytes


class BackupFile(typing.NamedTuple):
    name: str
    data: bytes


class BackupNameGenerator:
    def __init__(self):
        self.taken_names: set[str] = set()

    async def _get_random_name(self, *, recursive_tries: int = 5, total_tries: int = 0) -> str:
        tries = recursive_tries
        while tries >= 0:
            name = str(uuid.uuid4().int)
            if name not in self.taken_names:
                return name
            tries -= 1

        if recursive_tries > 0:
            await asyncio.sleep(1)
            return await self._get_random_name(recursive_tries=recursive_tries-1, total_tries=total_tries+5)

        raise RuntimeError(f"Couldn't generate a random name in {total_tries} tries")

    async def check(self, name: str) -> str:
        if name not in self.taken_names:
            self.taken_names.add(name)
            return name

        random_name = await self._get_random_name()
        self.taken_names.add(random_name)
        return random_name


class Owner(commands.Cog, name="owner"):
    """
    Owner commands
    """

    def __init__(self, bot: DiscordChan):
        self.bot = bot

        self.backup_channel: MessageableGuildChannel | None = None
        self.backup_collected: list[BackupFile] = []
        self.backup_postpone_queue: list[asyncio.Task] = []
        self.backup_name_generator = BackupNameGenerator()

    async def cog_check(self, ctx: commands.Context) -> bool:  # type: ignore (this method is allowed to be sync and async)
        if not await self.bot.is_owner(ctx.author):
            raise commands.NotOwner("You do not own this bot")
        return True

    async def _backup_postpone_task(self, message: discord.Message):
        # wait for discord to populate embeds
        await asyncio.sleep(5)
        refreshed_message = await message.channel.fetch_message(message.id)
        logger.info(f"Post postponed message refresh: {len(refreshed_message.embeds)=} {len(message.embeds)=}")
        if len(refreshed_message.embeds) > 0:
            await message.reply(f"Found delayed embeds: {len(refreshed_message.embeds)}")
            await self.backup_message_processor(refreshed_message, was_postpone=True)

    @commands.Cog.listener("on_message")
    async def backup_message_processor(self, message: discord.Message, *, was_postpone: bool = False):
        if self.backup_channel is None:
            return

        if message.author.bot:
            return

        if message.channel.id != self.backup_channel.id:
            return

        if len(message.embeds) == 0 and not was_postpone:
            logger.info(f"Postponing message {message.id} {len(message.embeds)=}")
            self.backup_postpone_queue.append(asyncio.create_task(self._backup_postpone_task(message)))
            return

        for embed in message.embeds:
            match embed.type:
                case "image":
                    link = embed.thumbnail.url
                case "gifv":
                    link = embed.video.url
                case _:
                    return await message.reply(f"Unsupported embed type: {embed.type}")
                
            if link is None:
                return await message.reply(f"Link was None in embed")

            try:
                url = yarl.URL(link)
                data, _ = await get_bytes(link)
                self.backup_collected.append(BackupFile(name=url.name, data=data))
            except Exception as e:
                return await message.reply(f"Error collecting: {e}")

            await message.reply(f"Collected {url.name}")

    @commands.group(name="dbg")
    async def debug_command(self, ctx: SubContext):
        """
        various debug commands
        """
        return

    @debug_command.group(name="backup", invoke_without_command=True)
    async def backup_command(self, ctx: SubContext):
        self.backup_channel = ctx.channel
        await ctx.confirm("Backup started")

    @backup_command.command(name="post")
    async def backup_post(self, ctx: SubContext):
        self.backup_channel = None

        with tempfile.TemporaryDirectory() as temp_dir:
            backup_zip_path = Path(temp_dir) / "backup.zip"

            with zipfile.ZipFile(backup_zip_path, "x") as backup_zip:
                for file in self.backup_collected:
                    file_as_path = Path(file.name)
                    file_name = file_as_path.with_suffix("").name
                    file_extension = file_as_path.suffix
                    file_name = await self.backup_name_generator.check(file_name)

                    backup_zip.writestr(file_name + file_extension, file.data)

            self.backup_collected = []

            try:
                await ctx.send("backup:", file=discord.File(backup_zip_path, filename="backup.zip"))
            except Exception as e:
                await ctx.send(f"Failure sending backup file, path is: {backup_zip_path}")
                await ctx.prompt("Done?")

    @debug_command.command()
    async def error(self, ctx: SubContext):
        raise Exception("test error")

    @debug_command.command()
    async def enable(self, ctx: SubContext, *, cmd):
        command = self.bot.get_command(cmd)

        if command is None:
            return await ctx.send("Command not found")

        command.enabled = True
        await ctx.confirm("Command enabled")

    @debug_command.command()
    async def disable(self, ctx: SubContext, *, cmd):
        command = self.bot.get_command(cmd)

        if command is None:
            return await ctx.send("Command not found")

        command.enabled = False
        await ctx.confirm("Command disabled")

    @debug_command.command()
    async def resend_file(self, ctx: SubContext, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.read()

        try:
            filename = url.split("/")[-1]
        except IndexError:
            filename = None

        await ctx.send(file=discord.File(BytesIO(data), filename))

    @debug_command.command()
    async def purge_feature(
        self, 
        ctx: SubContext, 
        feature: typing.Annotated[discord_chan.Feature, EnumConverter(discord_chan.Feature)]
    ):
        await self.bot.feature_manager.purge_feature(feature)
        await ctx.confirm("Feature purged")


async def setup(bot):
    await bot.add_cog(Owner(bot))
