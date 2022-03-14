#  Copyright © 2020 StarrFox
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
