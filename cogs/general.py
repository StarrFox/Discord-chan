import discord
from discord.ext import commands
import typing
import io
from datetime import datetime
from extras import checks
import json
from extras import utils

class general(commands.Cog):
    """General use commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def say(self, ctx, channel: typing.Optional[discord.TextChannel] = None, *, message: commands.clean_content()):
        """Have the bot say something"""
        if not channel:
            return await ctx.send(message)
        auth = ctx.author
        checks = [
            auth.id in self.bot.owners,
            auth.guild_permissions.administrator,
            auth.guild_permissions.manage_channels
        ]
        if any(checks):
            return await channel.send(message)
        await ctx.message.add_reaction("\u274c")

    @commands.command()
    async def ping(self, ctx):
        """Check bot ping and latency"""
        process_time = round(((datetime.utcnow()-ctx.message.created_at).total_seconds())*1000)
        e = discord.Embed(
            color=discord.Color.blurple()
        )
        e.add_field(
            name="**Latency:**",
            value=f"{round(self.bot.latency*1000)}ms"
        )
        e.add_field(
            name="**Process time:**",
            value=f"{process_time}ms",
            inline=False
        )
        e.set_thumbnail(url=ctx.me.avatar_url)
        await ctx.send(embed=e)

    @commands.command()
    async def invite(self, ctx):
        """Invite the bot to your server"""
        invite0 = f"https://discordapp.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=0&scope=bot"
        invite8 = f"https://discordapp.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=1949690966&scope=bot"
        message = f"**With perms:**\n<{invite8}>\n**Without perms (some things may not work):**\n<{invite0}>"
        await ctx.send(message)

    @commands.command(aliases=['msg'])
    @checks.has_permissions(administrator=True)
    async def quote(self, ctx, user: discord.Member, *, message: commands.clean_content()):
        """Send a message as someone else"""
        hook = await ctx.channel.create_webhook(name=user.display_name)
        await hook.send(message, avatar_url=user.avatar_url_as(format='png'))
        await hook.delete()

    @commands.group(invoke_without_command=True)
    async def raw(self, ctx):
        """
        Base raw command
        just sends help for raw
        """
        await ctx.send_help("raw")

    async def send_raw(self, ctx, message):
        to_send = json.dumps(message, indent=4)
        to_send = discord.utils.escape_markdown(to_send)
        await self.bot.paginate(to_send, ctx, lang='json')

    @raw.command(aliases=['msg'])
    async def message(self, ctx, channel: discord.TextChannel, messageid: int):
        """
        Raw message object
        """
        try:
            message = await self.bot.http.get_message(channel.id, messageid)
        except:
            return await ctx.send("Invalid message id")
        await self.send_raw(ctx, message)

    @raw.command()
    async def channel(self, ctx, channel: discord.TextChannel):
        """
        Raw channel object
        """
        try:
            message = await self.bot.http.get_channel(channel.id)
        except:
            return await ctx.send("Invalid channel id")
        await self.send_raw(ctx, message)

    @raw.command()
    async def member(self, ctx, member: discord.Member):
        """
        Raw member object
        """
        try:
            message = await self.bot.http.get_member(member.guild.id, member.id)
        except:
            return await ctx.send("Invalid member id")
        await self.send_raw(ctx, message)

    @raw.command()
    async def user(self, ctx, userid: int):
        """
        Raw user object
        """
        try:
            message = await self.bot.http.get_user(userid)
        except:
            return await ctx.send("Invalid user id")
        await self.send_raw(ctx, message)

    @raw.command(aliases=['server'])
    async def guild(self, ctx, guildid: int):
        """
        Raw guild object
        """
        try:
            message = await self.bot.http.get_guild(guildid)
        except:
            return await ctx.send("Invalid guild id")
        await self.send_raw(ctx, message)

    @raw.command(name='invite')
    async def raw_invite(self, ctx, invite: str):
        """
        Raw invite object
        """
        try:
            message = await self.bot.http.get_invite(invite.split('/')[-1])
        except:
            return await ctx.send("Invalid invite")
        await self.send_raw(ctx, message)

    @commands.command(aliases=["avy", "pfp"])
    async def avatar(self, ctx, member: discord.Member = None):
        """
        Check someone's avatar, defaults to author
        """
        if member is None:
            member = ctx.author
        e = discord.Embed(title=str(member), url=str(member.avatar_url_as(size=1024)))
        e.set_image(url=str(member.avatar_url))
        await ctx.send(embed=e)

    @commands.command(hidden=True)
    async def ham(self, ctx):
        await ctx.send("https://youtu.be/yCei3RrNSmY")

    @commands.command(hidden=True)
    async def weeee(self, ctx):
        await ctx.send("https://www.youtube.com/watch?v=2Y1iPavaOTE")

    @commands.command(hidden=True)
    async def chika(self, ctx):
        await ctx.send("https://www.youtube.com/watch?v=iS2s9deFClY")

def setup(bot):
    bot.add_cog(general(bot))
