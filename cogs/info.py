import discord
from discord.ext import commands

import humanize
from datetime import datetime

from extras.paginator import paginator
from extras import utils

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
        msg = f"A discord bot by StarrFox#6312, {ctx.prefix}help to see commands and " \
        f"{ctx.prefix}support to join the support server"
        await ctx.send(msg)

    @commands.command(aliases=['ui'])
    async def userinfo(self, ctx, member: discord.Member = None):
        """Get info on a guild member"""
        if not member:
            member = ctx.author
        joined = humanize.naturaldate(member.joined_at)
        joined_dis = humanize.naturaldate(member.created_at)
        #top_role = member.top_role.name
        #top_role_pos = (ctx.message.guild.roles[::-1].index(member.top_role))+1
        e = discord.Embed(color=member.color)
        e.add_field(name="Name:", value=str(member))
        e.add_field(name="ID:", value=member.id)
        e.add_field(name="Joined guild:", value=joined)
        e.add_field(name="Joined discord:", value=joined_dis)
        e.set_thumbnail(url=str(member.avatar_url))
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
        e.set_thumbnail(url=str(guild.icon_url))
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
