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
from discord.ext import commands

from discord_chan import EmbedDictPaginator, SnipeMode, DiscordChan, DCMenuPages, NormalPageSource


class Snipe(commands.Cog, name='snipe'):

    def __init__(self, bot: DiscordChan):
        self.bot = bot

    @staticmethod
    def get_dict_from_snipes(snipes: typing.Iterable) -> dict:
        res = {}

        for snipe in snipes:
            res[str(snipe)] = shorten(snipe.content, 1_024, placeholder='...')  # Field value limit

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
            mode = SnipeMode[mode]
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
        else:
            snipes = self.bot.snipes[channel.guild.id][channel.id]
            for _filter in filters:
                snipes = list(filter(_filter, snipes))

        return snipes

    # # TODO: replace with snipe2 when it's working nicely
    # @commands.group(name='snipe', invoke_without_command=True)
    # async def snipe_command(self,
    #                         ctx: commands.Context,
    #                         index: typing.Optional[int] = 0,
    #                         channel: typing.Optional[discord.TextChannel] = None,
    #                         member: typing.Optional[discord.Member] = None,
    #                         *, text: str = None
    #                         ):
    #     """Snipe messages deleted/edited in a channel
    #     You can also search for a specific channel and/or author and/or text
    #     Ex:
    #     "snipe #general @starrfox hello" will find snipes from starrfox in general containing the text "hello"
    #     "snipe #general @starrfox" will find snipes from starrfox in general
    #     "snipe @starrfox" will find snipes from starrfox in current channel
    #     "snipe #general" will find snipes in general
    #     "snipe" with find snipes in the current channel
    #     """
    #     channel = channel or ctx.channel
    #
    #     if not ctx.channel.is_nsfw() and channel.is_nsfw():
    #         return await ctx.send("You cannot snipe a nsfw channel from a non-nsfw channel.")
    #
    #     if not channel.permissions_for(ctx.author).read_messages:
    #         return await ctx.send("You need permission to view a channel to snipe from it.")
    #
    #     snipes = self.get_snipes(
    #         ctx,
    #         channel=channel,
    #         authors=[member] if member else None,
    #         contains=text
    #     )
    #
    #     if not snipes:
    #         return await ctx.send("No snipes found.")
    #
    #     try:
    #         snipe = snipes[index]
    #     except IndexError:
    #         return await ctx.send("Index out of bounds.")
    #
    #     e = discord.Embed(title=str(snipe), description=snipe.content)
    #
    #     e.set_footer(text=f'{index}/{len(snipes) - 1}')
    #
    #     return await ctx.send(embed=e)
    #
    # @snipe_command.command(name='list')
    # async def snipe_list(self,
    #                      ctx: commands.Context,
    #                      channel: typing.Optional[discord.TextChannel] = None,
    #                      member: typing.Optional[discord.Member] = None,
    #                      *, text: str = None
    #                      ):
    #     """list Sniped messages deleted/edited in a channel
    #     You can also search for a specific channel or/and author or/and text
    #     Ex:
    #     "snipe list #general @starrfox hello" will find snipes from starrfox in general containing the text "hello"
    #     "snipe list #general @starrfox" will find snipes from starrfox in general
    #     "snipe list @starrfox" will find snipes from starrfox in current channel
    #     "snipe list #general" will find snipes in general
    #     "snipe list" with find snipes in the current channel
    #     """
    #     channel = channel or ctx.channel
    #
    #     if not ctx.channel.is_nsfw() and channel.is_nsfw():
    #         return await ctx.send("You cannot snipe a nsfw channel from a non-nsfw channel.")
    #
    #     if not channel.permissions_for(ctx.author).read_messages:
    #         return await ctx.send("You need permission to view a channel to snipe from it.")
    #
    #     snipes = self.get_snipes(
    #         ctx,
    #         channel=channel,
    #         authors=[member] if member else None,
    #         contains=text
    #     )
    #
    #     if not snipes:
    #         return await ctx.send("No snipes found.")
    #
    #     paginator = EmbedDictPaginator(max_fields=10)
    #
    #     data = self.get_dict_from_snipes(snipes)
    #
    #     paginator.add_fields(data)
    #
    #     interface = EmbedDictInterface(self.bot, paginator, owner=ctx.author)
    #
    #     await interface.send_to(ctx)

    # Todo: test --index, --guild, --server, and --list
    # Make sure can't snipe nsfw with guild or unreadable channels
    # @commands.command(cls=flags.FlagCommand, name='snipe')
    @commands.command(name='snipe')
    async def snipe_command(self, ctx: commands.Context, *, options: str = ''):
        """
        Normal snipe but with command line arg parsing

        --users: List of user ids that authored the snipe
        --channel: Channel id to snipe from
        --server: Snipe from the entrie server instead of just a channel
        --before: Message id that snipes must be before
        --after: Message id that snipes must be after
        --index: Index to show from returned snipes, defaults to 0
        --list: Show all snipes found instead of one
        --mode: Mode of the snipes (edited, deleted, purged)
        --contains: String that must be in the snipes

        Nsfw (if this isn't one) and channel's you can't view are auto filtered out.
        """
        # Todo: see about switching to using discord-flags?
        parser = argparse.ArgumentParser(add_help=False)

        parser.add_argument('--authors', nargs='+', type=int)
        parser.add_argument('--channel', default=ctx.channel.id, type=int)
        parser.add_argument('--guild', '--server', action='store_true')
        parser.add_argument('--before', type=int)
        parser.add_argument('--after', type=int)
        parser.add_argument('--index', default=0, type=int)
        parser.add_argument('--list', action='store_true')
        # Todo: --diff arg using diff lib; perhaps use ```diff? inconsistent with code blocks
        parser.add_argument('--mode', choices=['deleted', 'purged', 'edited'])
        parser.add_argument('--contains', nargs='+')

        try:
            args = parser.parse_args(shlex.split(options))
        except (Exception, SystemExit) as e:
            return await ctx.send(str(e))

        channel = ctx.guild.get_channel(args.channel)

        if channel is None:
            return await ctx.send('Channel not found.')

        # These are filtered out by get_snipes anyway
        if not ctx.channel.is_nsfw() and channel.is_nsfw():
            return await ctx.send('You cannot snipe a nsfw channel from a non-nsfw channel.')

        if not channel.permissions_for(ctx.author).read_messages:
            return await ctx.send('You need permission to view a channel to snipe from it.')

        snipes = self.get_snipes(
            ctx,
            channel=args.channel,
            guild=args.guild,
            authors=args.authors,
            before=args.before,
            after=args.after,
            mode=SnipeMode[args.mode],
            contains=args.contains
        )

        if not snipes:
            return await ctx.send("No snipes found for this search.")

        if args.list:
            paginator = EmbedDictPaginator(max_fields=10)

            data = self.get_dict_from_snipes(snipes)

            paginator.add_fields(data)

            source = NormalPageSource(paginator.pages)

            menu = DCMenuPages(source)

            await menu.start(ctx)

        else:
            try:
                snipe = snipes[args.index]
            except IndexError:
                return await ctx.send("Index out of bounds.")

            e = discord.Embed(title=str(snipe), description=snipe.content)

            e.set_footer(text=f'{args.index}/{len(snipes) - 1}')

            await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(Snipe(bot))
