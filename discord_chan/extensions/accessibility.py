import re

import discord
from discord.ext import commands

from discord_chan import (
    DiscordChan,
    SubContext,
)

CUSTOM_EMOJI_REGEX = (
    r"<(?P<animated>a)?:(?P<name>[0-9a-zA-Z_]{2,32}):(?P<id>[0-9]{15,21})>"
)


class Accessibility(commands.Cog, name="accessibility"):
    def __init__(self, bot: DiscordChan):
        self.bot = bot

    @commands.command(name="steal-these")
    async def steal_these(self, ctx: SubContext, message: discord.Message):
        """
        "Steal" the custom emojis from a message
        """
        emojis = []

        for group in re.finditer(CUSTOM_EMOJI_REGEX, message.content):
            groups = group.groups()
            emojis.append(
                discord.PartialEmoji(
                    animated=bool(groups[0]), name=groups[1], id=groups[2]
                )
            )

        if not emojis:
            return await ctx.send("No custom emojis found in message.")

        await ctx.send("\n".join([f"{e.name}: <{e.url!s}>" for e in emojis]))


async def setup(bot: DiscordChan):
    await bot.add_cog(Accessibility(bot))
