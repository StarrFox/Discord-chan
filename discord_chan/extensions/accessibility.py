import re

import discord
from discord.ext import commands

from discord_chan import DiscordChan, SubContext

CUSTOM_EMOJI_REGEX = (
    r"<(?P<animated>a)?:(?P<name>[0-9a-zA-Z_]{2,32}):(?P<id>[0-9]{15,21})>"
)


class Accessibility(commands.Cog, name="accessibility"):
    def __init__(self, bot: DiscordChan):
        self.bot = bot

    @commands.command(name="steal-these")
    async def steal_these(self, ctx: SubContext, message: discord.Message):
        """
        "Steal" the custom emojis/stickers from a message
        """
        emojis = []
        stickers = message.stickers

        for group in re.finditer(CUSTOM_EMOJI_REGEX, message.content):
            groups = group.groups()
            emojis.append(
                discord.PartialEmoji(
                    animated=bool(groups[0]), name=groups[1], id=int(groups[2])
                )
            )

        if not emojis and not stickers:
            return await ctx.send("No custom emojis/stickers found in message")

        if emojis:
            emoji_message = "Emojis:\n" + "\n".join(
                [f"{e.name}: <{e.url!s}>" for e in emojis]
            )
        else:
            emoji_message = ""

        if stickers:
            sticker_message = "Stickers:\n" + "\n".join(
                [f"{s.name}: <{s.url!s}>" for s in stickers]
            )
        else:
            sticker_message = ""

        await ctx.send(f"{emoji_message}\n{sticker_message}")


async def setup(bot: DiscordChan):
    await bot.add_cog(Accessibility(bot))
