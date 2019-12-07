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

import discord
import humanize
from bot_stuff.utils import get_prolog_pager
from discord.ext import commands
from jishaku.paginators import WrappedPaginator, PaginatorInterface


class info(commands.Cog):
    """Informational commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def support(self, ctx: commands.Context):
        """Links to the support server"""
        await ctx.send("<https://discord.gg/WsgQfxC>")

    @commands.command()
    async def source(self, ctx: commands.Context):
        """Get the bot's source link"""
        await ctx.send("<https://github.com/StarrFox/Discord-chan>")

    @commands.command()
    async def about(self, ctx: commands.Context):
        """View bot info"""
        bot = self.bot

        data = {
            'id': bot.user.id,
            'owner': 'StarrFox#6312',
            'created': humanize.naturaldate(bot.user.created_at)
        }

        events_cog = bot.get_cog('events')

        if events_cog:
            data.update({
                'events seen': sum(events_cog.socket_events.values())
            })

        interface = get_prolog_pager(self.bot, {bot.user.name: data}, ctx.author)

        await interface.send_to(ctx)

    @commands.command(aliases=['ui'])
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        """Get info on a guild member"""
        member = member or ctx.author

        data = {
            'id': member.id,
            'top role': member.top_role.name,
            'joined guild': humanize.naturaldate(member.joined_at),
            'joined discord': humanize.naturaldate(member.created_at)
        }

        interface = get_prolog_pager(self.bot, {member.name: data}, ctx.author)

        await interface.send_to(ctx)

    @commands.command(aliases=['si', 'gi', 'serverinfo'])
    async def guildinfo(self, ctx: commands.Context):
        """Get info on a guild"""
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

        interface = get_prolog_pager(self.bot, {guild.name: data}, ctx.author)

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
    async def message(self, ctx: commands.Context, channel: discord.TextChannel, messageid: int):
        """
        Raw message object
        """
        try:
            data = await self.bot.http.get_message(channel.id, messageid)
        except discord.errors.NotFound:
            return await ctx.send("Invalid message id")
        await self.send_raw(ctx, data)

    @raw.command()
    async def channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """
        Raw channel object
        """
        try:
            data = await self.bot.http.get_channel(channel.id)
        except discord.errors.NotFound:
            return await ctx.send("Invalid channel id")
        await self.send_raw(ctx, data)

    @raw.command()
    async def member(self, ctx: commands.Context, member: discord.Member):
        """
        Raw member object
        """
        try:
            data = await self.bot.http.get_member(member.guild.id, member.id)
        except discord.errors.NotFound:
            return await ctx.send("Invalid member id")
        await self.send_raw(ctx, data)

    @raw.command()
    async def user(self, ctx: commands.Context, userid: int):
        """
        Raw user object
        """
        try:
            data = await self.bot.http.get_user(userid)
        except discord.errors.NotFound:
            return await ctx.send("Invalid user id")
        await self.send_raw(ctx, data)

    @raw.command(aliases=['server'])
    async def guild(self, ctx: commands.Context, guildid: int):
        """
        Raw guild object
        """
        try:
            data = await self.bot.http.get_guild(guildid)
        except discord.errors.NotFound:
            return await ctx.send("Invalid guild id")
        await self.send_raw(ctx, data)

    @raw.command(name='invite')
    async def raw_invite(self, ctx: commands.Context, invite: str):
        """
        Raw invite object
        """
        try:
            data = await self.bot.http.get_invite(invite.split('/')[-1])
        except discord.errors.NotFound:
            return await ctx.send("Invalid invite")
        await self.send_raw(ctx, data)

    @commands.command(aliases=["avy", "pfp"])
    async def avatar(self, ctx: commands.Context, member: discord.Member = None):
        """
        Get a member's avatar
        """
        member = member or ctx.author
        await ctx.send(str(member.avatar_url_as(size=1024)))


def setup(bot):
    bot.add_cog(info(bot))
