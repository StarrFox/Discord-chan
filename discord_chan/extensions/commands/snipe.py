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

import argparse
import shlex
import typing
from textwrap import shorten

import discord
from discord.ext import commands, flags

from discord_chan import (SnipeMode, DiscordChan, DCMenuPages, snipe_parser,
                          NormalPageSource, EmbedFieldProxy, EmbedFieldsPageSource)


class Snipe(commands.Cog, name='snipe'):

    def __init__(self, bot: DiscordChan):
        self.bot = bot

    # Todo: --diff arg using diff lib; perhaps use ```diff? inconsistent with code blocks
    @snipe_parser
    @commands.command(cls=flags.FlagCommand, name='snipe')
    async def snipe_command(self, ctx: commands.Context, **options: dict):
        """
        Normal snipe but with command line arg parsing

        --authors: List of user ids that authored the snipe
        --channel: Channel id to snipe from
        --server: Snipe from the entrie server instead of just a channel
        --before: Message id that snipes must be before
        --after: Message id that snipes must be after
        --index: Index to show from returned snipes, defaults to 0
        --list: Show all snipes found instead of one
        --mode: Mode of the snipes (edited, deleted, purged)
        --contains: String that must be in the snipes

        Nsfw (if not used from one) and channels you can't view are auto filtered out.
        """

        if options['channel'] is None:
            channel = ctx.channel

        # These are filtered out by get_snipes anyway
        if not ctx.channel.is_nsfw() and channel.is_nsfw():
            return await ctx.send("You cannot snipe a nsfw channel from a non-nsfw channel.")

        if not channel.permissions_for(ctx.author).read_messages:
            return await ctx.send("You need permission to view a channel to snipe from it.")

        snipes = self.get_snipes(
            ctx,
            channel=channel,
            guild=options['guild'],
            authors=options['authors'],
            before=options['before'],
            after=options['after'],
            mode=SnipeMode[options['mode']] if options['mode'] else None,
            contains=options['contains']
        )

        if not snipes:
            return await ctx.send("No snipes found for this search.")

        if options['list']:
            proxies = self.get_proxy_fields(snipes)

            source = EmbedFieldsPageSource(proxies, per_page=10)

            menu = DCMenuPages(source)

            await menu.start(ctx)

        else:
            try:
                snipe = snipes[options['index']]
            except IndexError:
                return await ctx.send("Index out of bounds.")

            e = discord.Embed(title=str(snipe), description=snipe.content)

            e.set_footer(text=f"{options['index']}/{len(snipes) - 1}")

            await ctx.send(embed=e)

    @staticmethod
    def get_proxy_fields(snipes: typing.Iterable) -> list:
        res = []

        for snipe in snipes:
            # 1,024 is the field value limit
            res.append(EmbedFieldProxy(str(snipe), shorten(snipe.content, 1_024, placeholder='...')))

        return res

    def get_snipes(self,
                   ctx: commands.Context,
                   *,
                   channel: discord.TextChannel = None,
                   guild: bool = False,
                   authors: typing.List[discord.Member] = None,
                   before: int = None,
                   after: int = None,
                   mode: SnipeMode = None,
                   contains: str = None
                   ):

        if channel is None and guild is None:
            raise ValueError('Channel and Guild cannot both be None.')

        filters = [
            lambda snipe: snipe.channel.permissions_for(ctx.author).read_messages
        ]

        if not ctx.channel.is_nsfw():
            filters.append(lambda snipe: not snipe.channel.is_nsfw())

        if authors:
            filters.append(lambda snipe: snipe.author.id in authors)

        if before:
            filters.append(lambda snipe: snipe.id < before)

        if after:
            filters.append(lambda snipe: snipe.id > after)

        if mode:
            filters.append(lambda snipe: snipe.mode == mode)

        if contains:
            to_match = ' '.join(contains)
            filters.append(lambda snipe: to_match in snipe.content)

        if guild:
            snipes = []
            snipe_channels = self.bot.snipes[channel.guild.id]
            for channel_snipes in snipe_channels.values():
                filtered = channel_snipes
                for _filter in filters:
                    filtered = list(filter(_filter, filtered))
                snipes.extend(filtered)

            # need to be reorded by time, would be by channel otherwise
            snipes = sorted(snipes, key=lambda s: s.time)
        else:
            snipes = self.bot.snipes[channel.guild.id][channel.id]
            for _filter in filters:
                snipes = list(filter(_filter, snipes))

        return snipes


def setup(bot):
    bot.add_cog(Snipe(bot))
