import json
import discord
import humanize

from extras import utils
from datetime import datetime
from discord.ext import commands
from bot_stuff.utils import get_prolog_pager
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

    @commands.command(aliases=['about'])
    async def info(self, ctx: commands.Context):
        """View bot info"""
        bot = self.bot

        info = {
            'id': bot.user.id,
            'owner': 'StarrFox#6312',
            'created': humanize.naturaldate(bot.user.created_at)
        }
        
        events_cog = bot.get_cog('events')

        if events_cog:
            info.update({
                'events seen': sum(events_cog.socket_events.values())
            })

        interface = get_prolog_pager(self.bot, {bot.user.name: info}, ctx.author)

        await interface.send_to(ctx)

    @commands.command(aliases=['ui'])
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        """Get info on a guild member"""
        member = member or ctx.author

        info = {
            'id': member.id,
            'top role': member.top_role.name,
            'joined guild': humanize.naturaldate(member.joined_at),
            'joined discord': humanize.naturaldate(member.created_at)
        }

        interface = get_prolog_pager(self.bot, {member.name: info}, ctx.author)

        await interface.send_to(ctx)

    @commands.command(aliases=['si', 'gi', 'serverinfo'])
    async def guildinfo(self, ctx: commands.Context):
        """Get info on a guild"""
        guild = ctx.guild
        bots = len([m for m in guild.members if m.bot])
        humans = guild.member_count - bots

        info = {
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

        interface = get_prolog_pager(self.bot, {guild.name: info}, ctx.author)

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
        except:
            return await ctx.send("Invalid message id")
        await self.send_raw(ctx, data)

    @raw.command()
    async def channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """
        Raw channel object
        """
        try:
            data = await self.bot.http.get_channel(channel.id)
        except:
            return await ctx.send("Invalid channel id")
        await self.send_raw(ctx, data)

    @raw.command()
    async def member(self, ctx: commands.Context, member: discord.Member):
        """
        Raw member object
        """
        try:
            data = await self.bot.http.get_member(member.guild.id, member.id)
        except:
            return await ctx.send("Invalid member id")
        await self.send_raw(ctx, data)

    @raw.command()
    async def user(self, ctx: commands.Context, userid: int):
        """
        Raw user object
        """
        try:
            data = await self.bot.http.get_user(userid)
        except:
            return await ctx.send("Invalid user id")
        await self.send_raw(ctx, data)

    @raw.command(aliases=['server'])
    async def guild(self, ctx: commands.Context, guildid: int):
        """
        Raw guild object
        """
        try:
            data = await self.bot.http.get_guild(guildid)
        except:
            return await ctx.send("Invalid guild id")
        await self.send_raw(ctx, data)

    @raw.command(name='invite')
    async def raw_invite(self, ctx: commands.Context, invite: str):
        """
        Raw invite object
        """
        try:
            data = await self.bot.http.get_invite(invite.split('/')[-1])
        except:
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
