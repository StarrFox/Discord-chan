import discord
from discord.ext import commands

import humanize
from datetime import datetime

from extras.paginator import paginator

class info(commands.Cog):
    """Informational commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def support(self, ctx):
        """Links to the support server"""
        await ctx.send("<https://discord.gg/WsgQfxC>")

    @commands.command()
    async def source(self, ctx):
        """Get the bot's source link"""
        await ctx.send("<https://github.com/StarrFox/Discord-chan>")

    @commands.command(aliases=['about'])
    async def info(self, ctx):
        """View bot info"""
        await ctx.send(
            f"""
            ```
            Owner: StarrFox#6312
            Guilds: {len(self.bot.guilds)}
            Channels: {len([c for c in self.bot.get_all_channels()])}
            Top role: #{(ctx.guild.roles[::-1].index(ctx.guild.me.top_role))+1} {ctx.guild.me.top_role.name}
            Up for: {self.bot.uptime-datetime.utcnow()}
            ```
            """
        )

    @commands.command(aliases=['ui'])
    async def userinfo(self, ctx, user: discord.Member = None):
        """Get info on a server member"""
        if not user:
            user = ctx.author
        joined = humanize.naturaldate(user.joined_at)
        joined_dis = humanize.naturaldate(user.created_at)
        top_role = user.top_role.name
        top_role_pos = (ctx.message.guild.roles[::-1].index(user.top_role))+1
        e = discord.Embed(color=user.color)
        e.add_field(name="Name#discrim", value=str(user))
        e.add_field(name="ID:", value=user.id)
        e.set_thumbnail(url=user.avatar_url)
        e.add_field(name="Joined guild:", value=joined)
        e.add_field(name="Joined discord:", value=joined_dis)
        e.add_field(name="Status:", value=f"Web: {user.web_status}\nDesktop: {user.desktop_status}\nMobile: {user.mobile_status}")
        e.add_field(name="Top role:", value=f"{top_role} in pos #{top_role_pos}")
        if len(user.roles)-1 > 0:
            e.add_field(name=f"{len(user.roles)-1} role(s):", value=", ".join([r.mention for r in user.roles if r != ctx.guild.default_role]))
        await ctx.send(embed=e)

    @commands.group(aliases=['si', 'gi', 'serverinfo'])
    async def guildinfo(self, ctx):
        """Get info on a guild"""
        guild = ctx.guild
        bots = 0
        humans = 0
        for member in guild.members:
            if member.bot:
                bots += 1
            else:
                humans += 1
        e = discord.Embed(color=discord.Color.blurple())
        e.set_thumbnail(url=guild.icon_url)
        e.add_field(name="ID:", value=guild.id)
        e.add_field(name="Owner:", value=str(guild.owner))
        e.add_field(name="Created:", value=humanize.naturaltime(guild.created_at))
        e.add_field(name="Role count:", value=len(guild.roles))
        e.add_field(name="Members:", value=f"Humans: {humans}\nBots: {bots}\nTotal: {humans + bots}")
        e.add_field(name="Channels:", value=f"Categories: {len(guild.categories)}\nText: {len(guild.text_channels)}\nVoice: {len(guild.voice_channels)}")
        await ctx.send(embed=e)

    @commands.command(aliases=['cp', 'checkperms'])
    async def checkperm(self, ctx, *, perm: str):
        """list every user with a certain perm"""
        perm = perm.replace(" ", "_")
        perm = perm.lower()
        pager = paginator(self.bot)
        lines = []
        x = 1
        members = ctx.guild.members
        members.reverse()
        for m in members:
            for item in m.guild_permissions:
                if item[0] == perm and item[1] is True:
                    lines.append(f"{x}. {m.name}")
                    x += 1
            if len(lines) == 20:
                dex = "\n".join(lines)
                e = discord.Embed(
                    title = f"**Users with the {perm} perm**",
                    description = dex,
                    color = discord.Color.blurple()
                )
                pager.add_page(data=e)
                lines = []
        if len(lines) != 0:
            dex = "\n".join(lines)
            e = discord.Embed(
                title = f"**Users with the {perm} perm**",
                description = dex,
                color = discord.Color.blurple()
            )
            pager.add_page(data=e)
        if len(pager.pages) != 0:
            await pager.do_paginator(ctx)

def setup(bot):
    bot.add_cog(info(bot))
