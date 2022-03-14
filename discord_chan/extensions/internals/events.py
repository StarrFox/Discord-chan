#  Copyright © 2019 StarrFox
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

from collections import Counter

import discord
from discord.ext import commands

from discord_chan import DiscordChan, Snipe, SnipeMode


class Events(commands.Cog, name="events"):
    def __init__(self, bot: DiscordChan):
        self.bot = bot
        self.socket_events = Counter()
        self.command_uses = Counter()

    @commands.Cog.listener()
    async def on_socket_response(self, message):
        self.socket_events[message.get("t")] += 1

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        self.command_uses[ctx.command] += 1

    def attempt_add_snipe(self, message: discord.Message, mode: str):
        try:
            mode = SnipeMode[mode]
        except KeyError:
            raise ValueError(f"{mode} is not a valid snipe mode.")
        if message.content:
            snipe = Snipe(message, mode)
            self.bot.snipes[message.guild.id][message.channel.id].appendleft(snipe)

    @commands.Cog.listener("on_message_delete")
    async def snipe_delete(self, message: discord.Message):
        self.attempt_add_snipe(message, "deleted")

    @commands.Cog.listener("on_bulk_message_delete")
    async def bulk_snipe_delete(self, messages: [discord.Message]):
        for message in messages:
            self.attempt_add_snipe(message, "purged")

    @commands.Cog.listener("on_message_edit")
    async def snipe_edit(self, before: discord.Message, after: discord.Message):
        if before.content != after.content:
            self.attempt_add_snipe(before, "edited")


async def setup(bot):
    await bot.add_cog(Events(bot))
