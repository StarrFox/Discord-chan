import re
from enum import Enum, StrEnum

import discord
from discord.ext import commands
from PIL.Image import Image
from aexaroton.errors import ExarotonError
from aexaroton.server import Server as MinecraftServer

from . import utils
from .image import FileTooLarge, InvalidImageType, url_to_image
from discord_chan.bot import DiscordChan


class Weekday(StrEnum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"

    mon = monday
    tues = tuesday
    wed = wednesday
    thurs = thursday
    sat = saturday
    sun = sunday


class ImageFormat(StrEnum):
    png = "png"
    gif = "gif"
    jpeg = "jpeg"
    webp = "webp"


class EnumConverter(commands.Converter):
    def __init__(self, enum: type[Enum]):
        self.enum = enum
        self.names = list(map(lambda variant: variant.name, list(enum)))

    async def convert(self, ctx: commands.Context, argument: str):
        try:
            return self.enum[argument]
        except KeyError:
            raise commands.BadArgument(f"{argument} is not in {', '.join(self.names)}")

    def display(self) -> str:
        return ",".join(self.names)


WeekdayConverter = EnumConverter(Weekday)
ImageFormatConverter = EnumConverter(ImageFormat)


class BetweenConverter(commands.Converter):
    def __init__(self, lower_limit: int, upper_limit: int):
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit

    async def convert(self, ctx: commands.Context, argument: str) -> int:
        try:
            converted_argument = int(argument)
        except ValueError:
            raise commands.BadArgument(f"{argument} is not a valid number")
        if self.lower_limit <= converted_argument <= self.upper_limit:
            return converted_argument

        raise commands.BadArgument(
            f"{argument} is not between {self.lower_limit} and {self.upper_limit}"
        )

    def display(self) -> str:
        return f"{self.lower_limit}-{self.upper_limit}"


class UnderConverter(commands.Converter):
    def __init__(self, under: int):
        self.under = under

    async def convert(self, ctx, argument: str) -> int:
        try:
            converted_argument = int(argument)
        except ValueError:
            raise commands.BadArgument(f"{argument} is not a valid number")

        if converted_argument < self.under:
            return converted_argument

        raise commands.BadArgument(f"{argument} is not under {self.under}")

    def display(self) -> str:
        return f"<{self.under}"


class OverConverter(commands.Converter):
    def __init__(self, over: int):
        self.over = over

    async def convert(self, ctx, argument: str) -> int:
        try:
            converted_argument = int(argument)
        except ValueError:
            raise commands.BadArgument(f"{argument} is not a valid number")

        if converted_argument > self.over:
            return converted_argument

        raise commands.BadArgument(f"{argument} is not over {self.over}")

    def display(self) -> str:
        return f">{self.over}"


class MaxLengthConverter(commands.Converter):
    def __init__(self, max_size: int = 2000):
        self.max_size = max_size

    async def convert(self, ctx: commands.Context, argument: str) -> str:
        if len(argument) <= self.max_size:
            return argument

        raise commands.BadArgument(f"Argument over max size of {self.max_size}")

    def display(self) -> str:
        return f"<={self.max_size}"


class BotConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> discord.Member:
        member = await commands.MemberConverter().convert(ctx, argument)

        if member.bot:
            return member

        raise commands.BadArgument("That member is not a bot")


class MinecraftServerConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> MinecraftServer:
        if not isinstance(ctx.bot, DiscordChan):
            raise RuntimeError("Context initialized with incorrect bot type")

        if ctx.bot.exaroton_client is not None:
            exaroton = ctx.bot.exaroton_client
        else:
            raise commands.BadArgument(f"Minecraft commands currently not enabled")
        
        try:
            result = await exaroton.get_server(argument)
        except ExarotonError:
            result = None
        
        if result is not None:
            return result
        
        all_servers = await exaroton.get_servers()

        for server in all_servers:
            if server.data.name.lower() == argument.lower():
                return server
            
            if server.data.address.lower() == argument.lower():
                return server

        raise commands.BadArgument(f"Could not find server with id/name/address: {argument}")

async def guild_default_minecraft_server(ctx: commands.Context):
    if not isinstance(ctx.bot, DiscordChan):
        raise RuntimeError("Context initialized with incorrect bot type")

    if ctx.guild is None:
        raise commands.NoPrivateMessage()

    minecraft_cog = ctx.bot.get_cog("Minecraft")

    if minecraft_cog is None:
        raise commands.CheckFailure("Minecraft commands not enabled")

    if not hasattr(minecraft_cog, "get_guild_default_server"):
        raise RuntimeError("Unexpected behavior")

    return await minecraft_cog.get_guild_default_server(ctx.guild.id) # type: ignore (I don't feel like making sure this exists and everything)


DefaultMinecraftServer = commands.parameter(
    default=guild_default_minecraft_server,
    displayed_default="Default server"
)


# TODO: add sticker support
class ImageUrlConverter(commands.Converter):
    """
    Attempts to convert an argument to an image url in the following order
    1. Member -> str(.avatar_url_as(static_format=png))
    2. Message -> str(message.attachments[0].url)/message.embeds[0].url
    3. Emoji -> str(.url)
    4. Url regex
    """

    def __init__(self, force_format: str | None = None):
        self.force_format = force_format

    async def convert(self, ctx: commands.Context, argument: str) -> str:
        try:
            member = await commands.MemberConverter().convert(ctx, argument)

        except commands.BadArgument:
            member = None

        if member:
            if self.force_format is None:
                return member.display_avatar.with_static_format("png").url

            else:
                # I couldn't get the type checking for this to work
                return member.display_avatar.with_static_format(self.force_format).url  # type: ignore

        try:
            message = await commands.MessageConverter().convert(ctx, argument)

        except commands.BadArgument:
            message = None

        if message:
            if message.attachments:
                return str(message.attachments[0].url)

            elif message.embeds:
                embed = message.embeds[0]

                if embed.type == "image":
                    if embed.url:
                        return embed.url

                elif embed.image:
                    # .url should always be set in this case
                    return embed.image.url  # type: ignore

            raise commands.BadArgument("Message has no attachments/embed images")

        try:
            emoji = await commands.PartialEmojiConverter().convert(ctx, argument)

        except commands.BadArgument:
            emoji = None

        if emoji:
            if not self.force_format:
                if emoji.is_custom_emoji:
                    return str(emoji.url)

            else:
                return (
                    f"https://cdn.discordapp.com/emojis/{emoji.id}.{self.force_format}"
                )

        url_regex = re.fullmatch(utils.link_regex, argument)

        if url_regex:
            return url_regex.string

        raise commands.BadArgument(
            f'"{argument}" is not a member, message, custom emoji, or url.'
        )


async def last_image_url(ctx: commands.Context) -> str:
    if ctx.message.attachments:
        return ctx.message.attachments[0].url

    async for message in ctx.history(limit=10):
        if message.attachments:
            return message.attachments[0].url

        if message.embeds:
            embed = message.embeds[0]

            if embed.type == "image":
                if embed.url:
                    return embed.url

            elif embed.image is not None:
                # this can happen sometimes, just ignore those embeds
                if embed.image.proxy_url is None:
                    raise commands.CheckFailure("No image attached or in history")

                return embed.image.proxy_url

    raise commands.CheckFailure("No image attached or in history")


LastImageUrl = commands.parameter(
    default=last_image_url,
    displayed_default="last image",
)


# TODO: add support for wand images
class ImageConverter(ImageUrlConverter):
    async def convert(self, ctx: commands.Context, argument: str) -> Image:  # type: ignore
        url = await super().convert(ctx, argument)

        try:
            return await url_to_image(url)

        except (FileTooLarge, InvalidImageType) as e:
            raise commands.BadArgument(str(e))


async def last_image(ctx: commands.Context):
    url = await last_image_url(ctx)
    try:
        return await url_to_image(url)

    except (FileTooLarge, InvalidImageType) as e:
        raise commands.BadArgument(str(e))


LastImage = commands.parameter(
    default=last_image,
    displayed_default="last image",
)


class EmbedConverter(commands.MessageConverter):
    async def convert(self, ctx: commands.Context, argument: str):  # type: ignore
        message = await super().convert(ctx, argument)

        if not message.embeds:
            raise commands.BadArgument("Message had no embed")

        return message.embeds[0]
