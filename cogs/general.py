import discord
from discord.ext import commands
import typing
import io
from datetime import datetime
from extras import checks
import json
from extas import utils

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
        invite8 = f"https://discordapp.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot"
        message = f"**With perms:**\n<{invite8}>\n**Without perms (some things may not work):**\n<{invite0}>"
        await ctx.send(message)

    @commands.command(aliases=['msg'])
    @checks.serverowner_or_permissions(administrator=True)
    async def quote(self, ctx, user: discord.Member, *, message: commands.clean_content()):
        """Send a message as someone else"""
        hook = await ctx.channel.create_webhook(name=user.display_name)
        await hook.send(message, avatar_url=user.avatar_url_as(format='png'))
        await hook.delete()

    @commands.command(aliases=['msgsource', 'msgsrc'])
    async def msgraw(self, ctx, id: int):
        """Get the raw message data"""
        try:
            message = await self.bot.http.get_message(ctx.channel.id, id)
        except:
            return await ctx.send("Invalid message id")
        json_msg = json.dumps(message, indent=4)
        json_msg = json_msg.replace("`", "`\u200b")
        await ctx.send(f"```json\n{json_msg}```")

def setup(bot):
    bot.add_cog(general(bot))
