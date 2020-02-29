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

from discord_chan import (PrologPaginator, ImageFormatConverter, PartitionPaginator,
                          BetweenConverter, DCMenuPages, NormalPageSource, checks,
                          DiscordChan, SubContext)


class General(commands.Cog, name='general'):
    """General use commands"""

    def __init__(self, bot: DiscordChan):
        self.bot = bot

    @commands.command()
    async def charinfo(self, ctx: commands.Context, *, charactors):
        """
        Convert charactors to name syntax
        """
        paginator = PartitionPaginator(prefix=None,
                                       suffix=None,
                                       max_size=300,
                                       wrap_on=('}',)
                                       )

        final = ''
        for char in charactors:
            name = unicodedata.name(char)
            final += '\\' + 'N{' + name + '}'

        paginator.add_line(final)

        source = NormalPageSource(paginator.pages)

        menu = DCMenuPages(source)

        await menu.start(ctx)

    # Todo: finish this
    @checks.cog_loaded('events')
    @commands.group(aliases=['pf'], invoke_without_command=True)
    async def prefixfinder(self, ctx: commands.Context, bot: discord.Member):
        await ctx.send('wip tm')

    @checks.cog_loaded('events')
    @prefixfinder.command(name='list')
    async def prefixfinder_list(self, ctx: commands.Context):
        return

    @commands.command()
    async def say(self, ctx: commands.Context, *, message: commands.clean_content()):
        """Have the bot say something"""
        await ctx.send(message)

    @commands.command()
    async def clean(self, ctx: SubContext, ammount: BetweenConverter(1, 100) = 10):
        """
        Delete's the bot's last <ammount> message(s)
        ammount must be between 1 and 100, defaults to 10
        """

        def check(message):
            return message.author == ctx.me

        can_mass_delete = ctx.channel.permissions_for(ctx.me).manage_messages

        await ctx.channel.purge(limit=ammount, check=check, bulk=can_mass_delete)
        await ctx.confirm()

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

    @commands.command(aliases=['mi', 'userinfo', 'ui'])
    async def memberinfo(self, ctx: commands.Context, member: discord.Member = None):
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

        source = NormalPageSource(paginator.pages)

        menu = DCMenuPages(source)

        await menu.start(ctx)

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

        source = NormalPageSource(paginator.pages)

        menu = DCMenuPages(source)

        await menu.start(ctx)

    @commands.group(invoke_without_command=True)
    async def raw(self, ctx: commands.Context):
        """
        Base raw command
        just sends help for raw
        """
        await ctx.send_help("raw")

    @staticmethod
    async def send_raw(ctx: commands.Context, data: dict):

        paginator = PartitionPaginator(prefix='```json', max_size=1985)

        to_send = json.dumps(data, indent=4)
        to_send = discord.utils.escape_mentions(to_send)

        paginator.add_line(to_send)

        source = NormalPageSource(paginator.pages)

        menu = DCMenuPages(source)

        await menu.start(ctx)

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
        
    @raw.command()
    async def role(self, ctx: commands.Context, role: discord.Role):
        """
        Raw role object
        """
        data = await self.bot.http.get_roles(role.guild.id)
        role_data = discord.utils.find(lambda d: d['id'] == role.id, data)
        await self.send_raw(ctx, role_data)

    @commands.command(hidden=True)
    async def ham(self, ctx: commands.Context):
        await ctx.send("https://youtu.be/yCei3RrNSmY")

    @commands.command(hidden=True)
    async def weeee(self, ctx: commands.Context):
        await ctx.send("https://www.youtube.com/watch?v=2Y1iPavaOTE")

    @commands.command(hidden=True)
    async def chika(self, ctx: commands.Context):
        await ctx.send("https://www.youtube.com/watch?v=iS2s9deFClY")

    @commands.command(hidden=True)
    async def otter(self, ctx: commands.Context):
        await ctx.send('<:otter:596576722154029072>')


def setup(bot):
    bot.add_cog(General(bot))
