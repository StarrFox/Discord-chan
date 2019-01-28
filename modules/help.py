import discord
from discord.ext import commands
import inspect
import itertools
import re
from extras.paginator import paginator

#Really bad help command

class help_command:

    def __init__(self, bot):
        self.bot = bot
        self.bl = [
            'help',
            'events',
            'logger',
            'owner'
        ]

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
        entries = sorted(ctx.bot.get_cog_commands(cog_name), key=lambda c: c.name)
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

'''
    async def all_commands(self, ctx):
        def key(c):
            return c.cog_name or '\u200bMisc'
        entries = sorted(ctx.bot.commands, key=key)
        for cog, commands in itertools.groupby(entries, key=key):
            can_use = [cmd for cmd in commands if (await cmd.can_run(ctx)) and not cmd.hidden]
            print(can_use)
            dex = self.bot.get_cog(cog)
            dex = inspect.getdoc(dex)
            embeds = []
            def init_e():
                e = discord.Embed(
                    title = f"{cog}'s commands",
                    description = dex,
                    color = discord.Color.blurple()
                )
                e.set_thumbnail(url=self.bot.user.avatar_url)
                return e
            e = init_e()
            for cmd in can_use:
                e.add_field(
                    name = cmd.signature,
                    value = cmd.short_doc,
                    inline = False
                )
                if len(e.fields) >= 5:
                    embeds.append(e)
                    e = init_e()
            embeds.append(e)
            return embeds
'''

def setup(bot):
    bot.add_cog(help_command(bot))

'''
    @commands.command(name='help')
    async def _help(self, ctx, *, command: str):
        """Shows this command"""
        try:
            if command is None:
                p = await HelpPaginator.from_bot(ctx)
            else:
                entity = bot.get_cog(command) or bot.get_command(command)
                if entity is None:
                    clean = command.replace('@', '@\u200b')
                    return await ctx.send(f'Command or category "{clean}" not found.')
                elif isinstance(entity, commands.Command):
                    p = await HelpPaginator.from_command(ctx, entity)
                else:
                    p = await HelpPaginator.from_cog(ctx, entity)
            await p.paginate()

class help_pager(paginator):

    @classmethod
    async def from_bot(self, ctx):
        def key(c):
            return c.cog_name or '\u200bMisc'

        entries = sorted(ctx.bot.commands, key=key)
        nested_pages = []
        per_page = 9

        # 0: (cog, desc, commands) (max len == 9)
        # 1: (cog, desc, commands) (max len == 9)
        # ...

        for cog, commands in itertools.groupby(entries, key=key):
            plausible = [cmd for cmd in commands if (await _can_run(cmd, ctx)) and not cmd.hidden]
            if len(plausible) == 0:
                continue

            description = ctx.bot.get_cog(cog)
            if description is None:
                description = discord.Embed.Empty
            else:
                description = inspect.getdoc(description) or discord.Embed.Empty

            nested_pages.extend((cog, description, plausible[i:i + per_page]) for i in range(0, len(plausible), per_page))

        self = cls(ctx, nested_pages, per_page=1) # this forces the pagination session
        self.prefix = cleanup_prefix(ctx.bot, ctx.prefix)

        # swap the get_page implementation with one that supports our style of pagination
        self.get_page = self.get_bot_page
        self._is_bot = True

        # replace the actual total
        self.total = sum(len(o) for _, _, o in nested_pages)
        return self
'''