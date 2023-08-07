import re

import discord
from discord.ext import commands
from PIL.Image import Image

from . import utils
from .image import FileTooLarge, InvalidImageType, url_to_image

WEEKDAYS = ["monday", "tuesday", "wendsday", "thursday", "friday", "saturday", "sunday"]

WEEKDAY_ABBRS = {d.replace("day", ""): d for d in WEEKDAYS}


class FetchedUser(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str):
        id_match = re.match(r"<@!?(\d+)>$", argument) or re.match(
            r"(\d{15,21})$", argument
        )

        if id_match:
            user_id = int(id_match.group(1))
            for mention in ctx.message.mentions:
                if mention.id == id_match:
                    return mention

            try:
                user = await ctx.bot.fetch_user(user_id)
            except (discord.NotFound, discord.HTTPException):
                user = None

            if user:
                return user

            raise commands.BadArgument(f'User "{user_id}" not found.')

        return await FetchedMember().convert(ctx, argument)


class FetchedMember(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> discord.Member:
        if ctx.guild is None:
            raise commands.BadArgument("Cannot fetch members from dms")

        id_match = re.match(r"<@!?([0-9]+)>$", argument) or re.match(
            r"([0-9]{15,21})$", argument
        )

        if id_match:
            user_id = int(id_match.group(1))
            try:
                member = await ctx.guild.fetch_member(user_id)
            except discord.HTTPException:
                # see lower commit on why we don't raise
                member = None

            if member:
                return member

        # someone could be named 15-21 numbers
        members = await ctx.guild.query_members(argument, cache=False)

        if members:
            return members[0]

        raise commands.BadArgument('Member "{}" not found'.format(argument))


class ImageFormatConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> str:
        if argument in ("png", "gif", "jpeg", "webp"):
            return argument
        else:
            raise commands.BadArgument(
                "{} is not a valid image format.".format(argument)
            )


class BetweenConverter(commands.Converter):
    def __init__(self, num1: int, num2: int):
        self.num1 = num1
        self.num2 = num2

    async def convert(self, ctx: commands.Context, argument: str) -> int:
        try:
            converted_argument = int(argument)
        except ValueError:
            raise commands.BadArgument("{} is not a valid number.".format(argument))
        if self.num1 <= converted_argument <= self.num2:
            return converted_argument

        raise commands.BadArgument(
            "{} is not between {} and {}".format(argument, self.num1, self.num2)
        )


class UnderConverter(commands.Converter):
    def __init__(self, under: int):
        self.under = under

    async def convert(self, _, argument: str) -> int:
        try:
            converted_argument = int(argument)
        except ValueError:
            raise commands.BadArgument(f"{argument} is not a valid number")

        if converted_argument < self.under:
            return converted_argument

        raise commands.BadArgument(f"{argument} is not under {self.under}")


class OverConverter(commands.Converter):
    def __init__(self, over: int):
        self.over = over

    async def convert(self, _, argument: str) -> int:
        try:
            converted_argument = int(argument)
        except ValueError:
            raise commands.BadArgument(f"{argument} is not a valid number")

        if converted_argument > self.over:
            return converted_argument

        raise commands.BadArgument(f"{argument} is not over {self.over}")


class MaxLengthConverter(commands.Converter):
    def __init__(self, max_size: int = 2000):
        self.max_size = max_size

    async def convert(self, ctx: commands.Context, argument: str) -> str:
        if len(argument) <= self.max_size:
            return argument

        raise commands.BadArgument("Argument over max size of {}".format(self.max_size))


class WeekdayConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> str:
        converted = str(argument).lower()

        if converted in WEEKDAYS:
            return converted

        if converted in WEEKDAY_ABBRS:
            return WEEKDAY_ABBRS[converted]

        raise commands.BadArgument("{} is not a valid weekday.".format(argument))


class BotConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> discord.Member:
        member = await FetchedMember().convert(ctx, argument)

        if member.bot:
            return member

        raise commands.BadArgument("That is not a bot.")


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
            member = await FetchedMember().convert(ctx, argument)

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

            raise commands.BadArgument("Message has no attachments/embed images.")

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
            '"{}" is not a member, message, custom emoji, or url.'.format(argument)
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
                assert embed.image.url is not None
                return embed.image.url

    raise commands.CheckFailure("No image attached or in history")


LastImageUrl = commands.parameter(
    default=last_image_url,
    displayed_default="last image",
)


class ImageConverter(ImageUrlConverter):
    async def convert(self, ctx: commands.Context, argument: str) -> Image:
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
    async def convert(self, ctx: commands.Context, argument: str):
        message = await super().convert(ctx, argument)

        if not message.embeds:
            raise commands.BadArgument("Message had no embed.")

        return message.embeds[0]
