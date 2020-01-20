# -*- coding: utf-8 -*-
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

import discord
import humanize
from discord.ext import commands
from jishaku.paginators import PaginatorInterface

import discord_chan


class Meta(commands.Cog, name='meta'):
    """Informational commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """
        Send's the bot's websocket latency
        """
        await ctx.send(f"\N{TABLE TENNIS PADDLE AND BALL} {round(ctx.bot.latency*1000)}ms")

    @commands.command()
    async def invite(self, ctx: commands.Context, bot: discord.Member = None):
        """
        Get the invite link for a bot,
        defaults to myself
        """
        bot = bot or ctx.me

        if not bot.bot:
            return await ctx.send('That member is not a bot.')

        url = discord.utils.oauth_url(bot.id)
        await ctx.send(url)

    @commands.command()
    async def support(self, ctx: commands.Context):
        """
        Links to the support server
        """
        await ctx.send(self.bot.config['general']['support_url'])

    @commands.command()
    async def source(self, ctx: commands.Context):
        """
        Links to the bot source
        """
        await ctx.send(self.bot.config['general']['source_url'])

    @commands.command()
    async def about(self, ctx: commands.Context):
        """
        View info of the bot
        """
        data = {
            'id': self.bot.user.id,
            'owner': 'StarrFox#6312',
            'created': humanize.naturaldate(self.bot.user.created_at),
            'uptime': humanize.naturaltime(self.bot.uptime),
            'dc version': discord_chan.__version__,
            'd.py version': discord.__version__
        }

        events_cog = self.bot.get_cog('events')

        if events_cog:
            data.update(
                {
                    'events seen': sum(events_cog.socket_events.values())
                }
            )

        # Todo: see if 20 is enough
        paginator = discord_chan.PrologPaginator(align_places=20)

        paginator.recursively_add_dictonary({self.bot.user.name: data})

        interface = PaginatorInterface(self.bot, paginator, owner=ctx.author)

        await interface.send_to(ctx)

    @commands.command()
    async def socketstats(self, ctx: commands.Context):
        """
        View soketstats of the bot
        """
        events_cog = self.bot.get_cog('events')

        if not events_cog:
            return await ctx.send('Events cog not loaded.')

        socket_events = events_cog.socket_events

        total = sum(socket_events.values())

        paginator = discord_chan.PrologPaginator()

        paginator.recursively_add_dictonary({f"{total} total": socket_events})

        interface = PaginatorInterface(self.bot, paginator, owner=ctx.author)

        await interface.send_to(ctx)


def setup(bot):
    bot.add_cog(Meta(bot))
