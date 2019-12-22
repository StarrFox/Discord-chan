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

import typing

import discord
from discord.ext import commands

from extras import checks


class general(commands.Cog):
    """General use commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def say(self,
                  ctx,
                  channel: typing.Optional[discord.TextChannel] = None,
                  *, message: commands.clean_content()):
        """Have the bot say something"""
        if not channel:
            return await ctx.send(message)
        auth = ctx.author
        _checks = [
            await self.bot.is_owner(ctx.author),
            auth.guild_permissions.administrator,
            auth.guild_permissions.manage_channels
        ]
        if any(_checks):
            return await channel.send(message)
        await ctx.message.add_reaction("\u274c")

    @commands.command()
    async def ping(self, ctx):
        """
        Send's the bot's websocket latency
        """
        await ctx.send(f"\N{TABLE TENNIS PADDLE AND BALL} {round(ctx.bot.latency*1000)}ms")

    @commands.command()
    async def invite(self, ctx):
        """Invite the bot to your server"""
        invite0 = f"https://discordapp.com/api/oauth2/authorize?client_id={self.bot.user.id}&" \
                  f"permissions=0&scope=bot"
        invite8 = f"https://discordapp.com/api/oauth2/authorize?client_id={self.bot.user.id}&" \
                  f"permissions=1949690966&scope=bot"
        message = f"**With perms:**\n<{invite8}>\n**Without perms (some things may not work):**\n<{invite0}>"
        await ctx.send(message)

    @commands.command(aliases=['msg'])
    @checks.has_permissions(manage_webhooks=True)
    @commands.bot_has_permissions(manage_webhooks=True)
    async def quote(self, ctx, user: discord.Member, *, message: commands.clean_content()):
        """Send a message as someone else"""
        hook = await ctx.channel.create_webhook(name=user.display_name)
        await hook.send(message, avatar_url=user.avatar_url_as(format='png'))
        await hook.delete()

    @commands.command(hidden=True)
    async def ham(self, ctx):
        await ctx.send("https://youtu.be/yCei3RrNSmY")

    @commands.command(hidden=True)
    async def weeee(self, ctx):
        await ctx.send("https://www.youtube.com/watch?v=2Y1iPavaOTE")

    @commands.command(hidden=True)
    async def chika(self, ctx):
        await ctx.send("https://www.youtube.com/watch?v=iS2s9deFClY")

    # TODO: add back clean command?

def setup(bot):
    bot.add_cog(general(bot))
