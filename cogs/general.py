import io
import json
import typing
import discord

from extras import utils, checks
from datetime import datetime
from discord.ext import commands

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
            await self.bot.is_owner(ctx.author),
            auth.guild_permissions.administrator,
            auth.guild_permissions.manage_channels
        ]
        if any(checks):
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
        invite0 = f"https://discordapp.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=0&scope=bot"
        invite8 = f"https://discordapp.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=1949690966&scope=bot"
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

def setup(bot):
    bot.add_cog(general(bot))
