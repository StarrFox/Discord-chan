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
import json
import unicodedata
from typing import Optional

import discord
import humanize
from discord.ext import commands
from jishaku.paginators import PaginatorInterface, WrappedPaginator

from discord_chan import PrologPaginator, ImageFormatConverter, PartitionPaginator


class General(commands.Cog, name='general'):
    """General use commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def charinfo(self, ctx: commands.Context, *, charactors):
        """
        Convert charactors to name syntax
        """
        paginator = PartitionPaginator(prefix='',
                                       suffix='',
                                       max_size=300,
                                       wrap_on=('}',),
                                       include_wrapped=True
                                       )

        final = ''
        for char in charactors:
            name = unicodedata.name(char)
            final += '\\' + 'N{' + name + '}'

        paginator.add_line(final)

        interface = PaginatorInterface(self.bot, paginator, owner=ctx.author)
        await interface.send_to(ctx)

    @commands.command()
    async def say(self, ctx: commands.Context, *, message: commands.clean_content()):
        """Have the bot say something"""
        await ctx.send(message)

    # Todo: test this
    @commands.command()
    async def clean(self, ctx: commands.Context, ammount: int):
        def check(message):
            return message.author == ctx.me

        can_mass_delete = ctx.channel.permissions_for(ctx.me).manage_messages

        await ctx.channel.purge(limit=ammount, check=check, bulk=can_mass_delete)

    # TODO: test this
    @commands.command(aliases=["avy", "pfp"])
    async def avatar(self,
                     ctx: commands.Context,
                     member: Optional[discord.Member] = None,
                     format: Optional[ImageFormatConverter] = 'png'):
        """
        Get a member's avatar
        """
        member = member or ctx.author
        await ctx.send(
            str(member.avatar_url_as(format=format))
        )

    @commands.command(aliases=['ui'])
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        """
        Get info on a guild member
        """
        member = member or ctx.author

        data = {
            'id': member.id,
            'top role': member.top_role.name,
            'joined guild': humanize.naturaldate(member.joined_at),
            'joined discord': humanize.naturaldate(member.created_at)
        }

        paginator = PrologPaginator()

        paginator.recursively_add_dictonary({member.name: data})

        interface = PaginatorInterface(self.bot, paginator, owner=ctx.author)

        await interface.send_to(ctx)

    @commands.command(aliases=['si', 'gi', 'serverinfo'])
    async def guildinfo(self, ctx: commands.Context):
        """
        Get info on a guild
        """
        guild = ctx.guild
        bots = len([m for m in guild.members if m.bot])
        humans = guild.member_count - bots

        data = {
            'id': guild.id,
            'owner': str(guild.owner),
            'created': humanize.naturaltime(guild.created_at),
            '# of roles': len(guild.roles),
            'members': {
                'humans': humans,
                'bots': bots,
                'total': guild.member_count
            },
            'channels': {
                'categories': len(guild.categories),
                'text': len(guild.text_channels),
                'voice': len(guild.voice_channels),
                'total': len(guild.channels)
            }
        }

        paginator = PrologPaginator()

        paginator.recursively_add_dictonary({guild.name: data})

        interface = PaginatorInterface(self.bot, paginator, owner=ctx.author)

        await interface.send_to(ctx)

    @commands.group(invoke_without_command=True)
    async def raw(self, ctx: commands.Context):
        """
        Base raw command
        just sends help for raw
        """
        await ctx.send_help("raw")

    async def send_raw(self, ctx: commands.Context, data: dict):

        paginator = WrappedPaginator(prefix='```json', max_size=1985)

        to_send = json.dumps(data, indent=4)
        to_send = discord.utils.escape_mentions(to_send)

        paginator.add_line(to_send)

        interface = PaginatorInterface(self.bot, paginator, owner=ctx.author)

        await interface.send_to(ctx)

    @raw.command(aliases=['msg'])
    async def message(self, ctx: commands.Context, message: discord.Message):
        """
        Raw message object,
        can provide channel with channel_id-message-id
        (shift-click copy id)
        """
        data = await self.bot.http.get_message(message.channel.id, message.id)
        await self.send_raw(ctx, data)

    @raw.command()
    async def channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """
        Raw channel object
        """
        data = await self.bot.http.get_channel(channel.id)
        await self.send_raw(ctx, data)

    @raw.command()
    async def member(self, ctx: commands.Context, member: discord.Member):
        """
        Raw member object
        """
        data = await self.bot.http.get_member(member.guild.id, member.id)
        await self.send_raw(ctx, data)

    @raw.command()
    async def user(self, ctx: commands.Context, userid: int):
        """
        Raw user object
        """
        try:
            data = await self.bot.http.get_user(userid)
        except discord.errors.NotFound:
            await ctx.send("Invalid user id")
        else:
            await self.send_raw(ctx, data)

    @raw.command(aliases=['server'])
    async def guild(self, ctx: commands.Context):
        """
        Raw guild object
        """
        data = await self.bot.http.get_guild(ctx.guild.id)
        await self.send_raw(ctx, data)

    @raw.command()
    async def invite(self, ctx: commands.Context, invite: str):
        """
        Raw invite object
        """
        # I don't use the invite converter to save api calls
        try:
            data = await self.bot.http.get_invite(invite.split('/')[-1])
        except discord.errors.NotFound:
            await ctx.send("Invalid invite.")
        else:
            await self.send_raw(ctx, data)

    @raw.command()
    async def emoji(self, ctx: commands.Context, emoji: discord.Emoji):
        """
        Raw emoji object
        """
        data = await self.bot.http.get_custom_emoji(emoji.guild.id, emoji.id)
        await self.send_raw(ctx, data)

    @commands.command(hidden=True)
    async def ham(self, ctx: commands.Context):
        await ctx.send("https://youtu.be/yCei3RrNSmY")

    @commands.command(hidden=True)
    async def weeee(self, ctx: commands.Context):
        await ctx.send("https://www.youtube.com/watch?v=2Y1iPavaOTE")

    @commands.command(hidden=True)
    async def chika(self, ctx: commands.Context):
        await ctx.send("https://www.youtube.com/watch?v=iS2s9deFClY")

    # Todo: get real emoji
    @commands.command(hidden=True)
    async def otter(self, ctx: commands.Context):
        await ctx.send(':otter-1:')


def setup(bot):
    bot.add_cog(General(bot))
