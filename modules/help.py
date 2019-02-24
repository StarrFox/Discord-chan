import discord
from discord.ext import commands
import inspect
import itertools
import re
from extras.paginator import paginator

class help_command(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.old_help = self.bot.remove_command('help')
        self.bl = [
            'help_command',
            'events',
            'logger',
            'owner'
        ]

    def cog_unload(self):
        self.bot.remove_command('help')
        self.bot.add_command(self.bot.old_help)

    @commands.command()
    async def help(self, ctx, *, command: str = None):
        """Shows this message"""
        if command in self.bl:
            return await ctx.send("Didn't find a command or cog matching that entry")
        embeds = None
        if not command:
            embeds = await self.all_commands(ctx)
        if not embeds:
            if self.bot.get_cog(command):
                embeds = await self.cog_embed(ctx, command)
            elif self.bot.get_command(command):
                embeds = await self.command_embed(ctx, command)
            else:
                return await ctx.send("Didn't find a command or cog matching that entry")
        pager = paginator(self.bot)
        for embed in embeds:
            pager.add_page(data=embed)
        await pager.do_paginator(ctx)

    async def cog_embed(self, ctx, cog):
        cog = self.bot.get_cog(cog)
        cog_name = cog.__class__.__name__
        entries = sorted(cog.get_commands(), key=lambda c: c.name)
        entries = [cmd for cmd in entries if (await cmd.can_run(ctx)) and not cmd.hidden]
        e = discord.Embed(
            title = f"Commands in {cog_name}",
            color = discord.Color.blurple()
        )
        e.set_thumbnail(url=self.bot.user.avatar_url)
        for cmd in entries:
            e.add_field(
                name = cmd.name,
                value = f"{cmd.signature}: {cmd.help}",
                inline = False
            )
        return e

    async def command_embed(self, ctx, command):
        command = self.bot.get_command(command)
        try:
            entries = sorted(command.commands, key=lambda c: c.name)
        except AttributeError:
            entries = []
        else:
            entries = [cmd for cmd in entries if (await cmd.can_run(ctx)) and not cmd.hidden]
        embeds = []
        def init_e():
            e = discord.Embed(color = discord.Color.blurple())
            e.add_field(
                name = command.signature,
                value = command.short_doc,
                inline = False
            )
            e.set_thumbnail(url=self.bot.user.avatar_url)
            return e
        e = init_e()
        for ent in entries:
            e.add_field(
                name = ent.signature,
                value = ent.short_doc,
                inline = False
            )
            if len(e.fields) >= 5:
                embeds.append(e)
                e = init_e()
        if e.fields:
            embeds.append(e)
        return embeds

    async def all_commands(self, ctx):
        embeds = []
        for cog in [cog for cog in self.bot.cogs if not cog.name in self.bl]:
            e = discord.Embed(
                title = cog.__class__.__name__,
                color = discord.Color.blurple()
            )
            e.set_thumbnail(url=self.bot.user.avatar_url)
            for cmd in cog.get_commands():
                e.add_field(
                    name = cog.name,
                    value = f"{cmd.signature}: {cmd.help}",
                    inline = False
                )
            embeds.append(e)
        return embeds

def setup(bot):
    bot.add_cog(help_command(bot))