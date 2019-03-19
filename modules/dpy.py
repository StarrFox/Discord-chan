from discord.ext import commands
from extras.fuzzy import finder as fuzzyfinder
import discord

import asyncio
import importlib
import inspect
import itertools
import os
import random
import re
import subprocess

# Source: https://github.com/EvieePy/EvieeBot/blob/master/modules/apis.py
# Nothing in this cog was made by me and has only been modified to work in my envioment
# It was added to this bot as a util for the discord.py server since the source bot is no longer active

class DPYSource:

    __slots__ = ('file', 'obj', 'parent', 'index', 'path', 'match')

    def __init__(self, **attrs):
        self.file = attrs.get('file')
        self.obj = attrs.get('obj')
        self.parent = attrs.get('parent')
        self.index = attrs.get('index')
        self.path = attrs.get('path')
        self.match = attrs.get('match')

class dpy(commands.Cog):
    """Commands pertaining to
    the discord.py server"""


    def __init__(self, bot):
        self.bot = bot
        self.rtfs_anchors = None
        self.rtfs_revision = None

        bot.loop.create_task(self._update_rtfs())

    async def get_rtfs_revision(self):
        cmd = r'git ls-remote https://github.com/Rapptz/discord.py --tags rewrite HEAD~1..HEAD --format="%s (%cr)"'
        if os.name == 'posix':
            cmd = cmd.format(r'\`%h\`')
        else:
            cmd = cmd.format(r'`%h`')
        revision = os.popen(cmd).read().strip()

        return revision.split()[0]

    def rtfs_embed(self, search, matches):
        if not matches:
            embed = discord.Embed(title=f'RTFS - <{search}>',
                                  description=f'Sorry no results were found for {search}\n\nTry being more specific.',
                                  colour=0x6dc9c9)
            embed.add_field(name='Discord.py Source:', value='https://github.com/Rapptz/discord.py/tree/rewrite/')
        else:
            matches = '\n'.join(matches)
            embed = discord.Embed(title=f'RTFS - <{search}>', description=f'{matches}', colour=0x6dc9c9)

        return embed

    async def _update_rtfs(self):
        while not self.bot.is_closed():
            try:
                revision = await self.get_rtfs_revision()
            except Exception:
                await asyncio.sleep(600)
                continue

            if not self.rtfs_revision:
                pass
            elif self.rtfs_revision == revision:
                await asyncio.sleep(3600)
                continue
            await self._rtfs_load()

    async def _rtfs_load(self):
        self.rtfs_revision = await self.get_rtfs_revision()

        anchors = []
        parent = None

        pf = r'def(.*?[a-zA-Z0-9])\(.*\)|async def(.*?[a-zA-Z0-9])\(.*\)'
        pc = r'class (.*[a-zA-Z0-9])[\:\(]'

        def pred(y):
            if inspect.isbuiltin(y):
                return

            try:
                return 'discord' in y.__name__
            except AttributeError:
                return False

        importlib.reload(discord)

        mods = inspect.getmembers(discord, pred) + inspect.getmembers(commands, pred)
        for x in mods:
            file = x[1].__name__.split('.')[-1]
            path = '/'.join(x[1].__name__.split('.')[:-1])

            try:
                src = inspect.getsourcelines(x[1])
            except TypeError:
                continue

            for index, line in enumerate(src[0]):
                orig = line

                if sum(1 for _ in itertools.takewhile(str.isspace, line)) > 4:
                    continue
                elif line == 0 or '__' in line:
                    continue

                line = line.lstrip(' ')
                match = re.match(pf, line)

                if match:
                    if sum(1 for _ in itertools.takewhile(str.isspace, orig)) < 4:
                        parent = None

                elif not match:
                    match = re.match(pc, line)
                    if match:
                        parent = match.group(1)

                try:
                    obj = match.group(1) or match.group(2)
                    obj = obj.lstrip()
                except AttributeError:
                    continue

                attrs = {'file': file, 'obj': obj, 'parent': parent if parent != obj else None, 'index': index,
                         'path': path,
                         'match': f'{file}.{parent if parent and parent != obj else ""}'
                                  f'{"." if parent and parent != obj else ""}{obj}'}

                anchor = DPYSource(**attrs)
                anchors.append(anchor)

        self.rtfs_anchors = anchors

    @commands.command(name='rtfs', aliases=['dsauce', 'dsource', 'dpysauce', 'dpysource'])
    async def _rtfs(self, ctx, *, source: str=None):
        """Retrieve source code for discord.py.
        Parameters
        ------------
        source: [Optional]
            The file, function, class, method or path to retrieve source for. Could be none to display
            the base URL.
        Examples
        ----------
        <prefix>rtfs <source>
            {ctx.prefix}rtfs bot.py
            {ctx.prefix}rtfs Guild.members
            {ctx.prefix}rtfs Guild
            {ctx.prefix}rtfs member
        """
        orig = source
        surl = 'https://github.com/Rapptz/discord.py/blob/rewrite/'
        to_return = []

        if source is None:
            return await ctx.send('https://github.com/Rapptz/discord.py/tree/rewrite/')

        if source.endswith('.py'):
            source = source.replace('.py', '').lower()

            matches = fuzzyfinder(source, [(a, a.file) for a in self.rtfs_anchors],
                                        key=lambda t: t[1], lazy=False)[:5]

            for f in matches:
                to_return.append(f'[{f[0].file}.py]({surl}{f[0].path}/{f[0].file}.py)')

        elif '.' in source:
            matches = fuzzyfinder(source, [(a, a.match) for a in self.rtfs_anchors], key=lambda t: t[1],
                                        lazy=False)[:5]

            if not matches:
                matches = fuzzyfinder(source, [(a, a.match.split('.', 1)[-1]) for a in self.rtfs_anchors],
                                            key=lambda t: t[1], lazy=False)[:5]

            for a in matches:
                a = a[0]
                to_return.append(f'[{a.match}]({surl}{a.path}/{a.file}.py#L{a.index + 1})')
        else:
            matches = fuzzyfinder(source, [(a, a.obj) for a in self.rtfs_anchors], key=lambda t: t[1],
                                        lazy=False)[:5]

            for a in matches:
                a = a[0]
                to_return.append(f'[{a.match}]({surl}{a.path}/{a.file}.py#L{a.index + 1})')

        to_return = set(to_return)
        await ctx.send(embed=self.rtfs_embed(orig, sorted(to_return, key=lambda a: len(a))))

def setup(bot):
    bot.add_cog(dpy(bot))
