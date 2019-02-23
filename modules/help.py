import discord
from discord.ext import commands
import inspect
import itertools
import re
from extras.paginator import paginator

#Really bad help command

class help_command(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.old_help = self.bot.remove_command('help')
        self.bl = [
            'help',
            'events',
            'logger',
            'owner'
        ]

    def cog_unload(self):
        self.bot.remove_command('help')
        self.bot.add_command(self.bot.old_help)

    @commands.command(name='help')
    async def _help(self, ctx, *, command: str = None):
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
        entries = sorted(cog.walk_commands(), key=lambda c: c.name)
        entries = [cmd for cmd in entries if (await cmd.can_run(ctx)) and not cmd.hidden]
        embeds = []
        def init_e():
            e = discord.Embed(
                title = f"{cog_name}'s commands",
                description = inspect.getdoc(cog),
                color = discord.Color.blurple()
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
        ext = self.bot.extensions.keys()
        ext = list(ext)
        for i in self.bl:
            i = "modules." + i
            ext.remove(i)
        les = []
        embeds = []
        for e in ext:
            les.append(await self.cog_embed(ctx, e.replace('modules.', '')))
        for le in les:
            for l in le:
                embeds.append(l)
        return embeds

def setup(bot):
    bot.add_cog(help_command(bot))