import datetime
import re
from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands.context import Context

from . import utils

WEEKDAYS = ["monday", "tuesday", "wendsday", "thursday", "friday", "saturday", "sunday"]

WEEKDAY_ABBRS = {d.replace("day", ""): d for d in WEEKDAYS}

TIME_REGEX = re.compile(
    r"(?P<days>\d+ ?d(ay)?s?)|(?P<months>\d+ ?mo(nth)?s?)|(?P<minutes>\d+ ?m(in)?(ute)?s?)|"
    r"(?P<years>\d+ ?y(ear)?s?)|(?P<seconds>\d+ ?s(ec)?(ond)?s?)|(?P<hours>\d+ ?h(our)?s?)|(?P<weeks>\d+ ?w(eek)?s?)"
)


TIME_TABLE = {
    "seconds": 1,
    "minutes": 60,
    "hours": 3600,
    "days": 86400,
    "weeks": 604800,
    "months": 2592000,
    "years": 31536000,
}


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

    def __init__(self, force_format: Optional[str] = None):
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


class EmbedConverter(commands.MessageConverter):
    async def convert(self, ctx: commands.Context, argument: str):
        message = await super().convert(ctx, argument)

        if not message.embeds:
            raise commands.BadArgument("Message had no embed.")

        return message.embeds[0]


class TimeConverter(commands.Converter):
    """
    Converts a time phrase to a number of seconds

    1min -> 60
    1m   -> 60
    2m   -> 120
    """

    async def convert(self, ctx: commands.Context, argument: str) -> int:
        match = TIME_REGEX.match(argument)

        if not match:
            raise commands.BadArgument(f"{argument} is not a valid time")

        total = 0

        digit_re = re.compile(r"\d+")

        for group, value in match.groupdict().items():
            if value is None:
                continue

            int_value = int(digit_re.match(value).group(0))  # type: ignore

            if group == "years":
                current_year = datetime.datetime.utcnow().year

                # Leap year
                if current_year % 4 == 0:
                    total += (TIME_TABLE["years"] * int_value) + TIME_TABLE["days"]

                else:
                    total += TIME_TABLE["years"] * int_value

            elif group == "months":
                now = datetime.datetime.utcnow()

                if now.month == 12:
                    next_month = now.replace(month=1, year=now.year + 1)

                else:
                    next_month = now.replace(month=now.month + 1)

                total += int((next_month - now).total_seconds())

            else:
                total += TIME_TABLE[group] * int_value

        return total
