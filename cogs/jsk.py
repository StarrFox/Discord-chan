from jishaku import cog
from jishaku.exception_handling import *

import asyncio
import collections
import contextlib
import datetime
import inspect
import itertools
import os
import os.path
import re
import sys
import time
import traceback
import typing

import discord
import humanize
from discord.ext import commands

from jishaku.codeblocks import Codeblock, CodeblockConverter
from jishaku.meta import __version__
from jishaku.models import copy_context_with
from jishaku.modules import ExtensionConverter, package_version
from jishaku.paginators import PaginatorInterface, WrappedFilePaginator, WrappedPaginator
from jishaku.repl import AsyncCodeExecutor, Scope, all_inspections, get_var_dict_from_ctx
from jishaku.shell import ShellReader
from jishaku.voice import BasicYouTubeDLSource, connected_check, playing_check, vc_check, youtube_dl

try:
    import psutil
except ImportError:
    psutil = None

#emojis
task = "<a:sonic:577005444191485952>"
done = "<a:dancin:582409853918511165>"
syntax_error = "<a:default:577017740016222229>"
timeout_error = "error:539157627385413633"
error = "<a:default:577017740016222229>"

def sub_get_var_dict_from_ctx(ctx, prefix: str = '_'):
    raw_var_dict = {
        'author': ctx.author,
        'bot': ctx.bot,
        'channel': ctx.channel,
        'ctx': ctx,
        'guild': ctx.guild,
        'message': ctx.message,
        'msg': ctx.message,
        'get': discord.utils.get,
        'send': ctx.send
    }
    return {f'{prefix}{k}': v for k, v in raw_var_dict.items()}

class reactor_sub(ReplResponseReactor):

    async def __aenter__(self):
        self.handle = self.loop.create_task(do_after_sleep(1, attempt_add_reaction, self.message, task))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.handle:
            self.handle.cancel()
        if not exc_val:
            await attempt_add_reaction(self.message, done)
            return
        self.raised = True
        if isinstance(exc_val, (asyncio.TimeoutError, subprocess.TimeoutExpired)):
            await attempt_add_reaction(self.message, timeout_error)
            await send_traceback(self.message.channel, 0, exc_type, exc_val, exc_tb)
        elif isinstance(exc_val, SyntaxError):
            await attempt_add_reaction(self.message, syntax_error)
            await send_traceback(self.message.channel, 0, exc_type, exc_val, exc_tb)
        else:
            await attempt_add_reaction(self.message, error)
            await send_traceback(self.message.author, 8, exc_type, exc_val, exc_tb)
        return True

class sub_jsk(cog.Jishaku):

    def __init__(self, bot):
        self.bot = bot
        self._scope = Scope()
        self.retain = True
        self.last_result = None
        self.start_time = datetime.datetime.now()
        self.tasks = collections.deque()
        self.task_count: int = 0
        self.arg_prefix = ''

    @commands.group(name="jishaku", aliases=["jsk"], hidden=True, invoke_without_command=True, ignore_extra=False)
    async def jsk(self, ctx):
        """
        The Jishaku debug and diagnostic commands.
        This command on its own gives a status brief.
        All other functionality is within its subcommands.
        """
        summary = [
            f"Jishaku: v{__version__}, loaded {humanize.naturaltime(self.load_time)}",
            f"Python: {sys.version}".replace("\n", ""),
            f"HostOS: {sys.platform}",
            f"Discord.py: v{package_version('discord.py')}",
            ""
        ]
        if psutil:
            proc = psutil.Process()
            with proc.oneshot():
                mem = proc.memory_full_info()
                summary.append(f"Memory: {humanize.naturalsize(mem.rss)} physical, "
                               f"{humanize.naturalsize(mem.vms)} virtual, "
                               f"{humanize.naturalsize(mem.uss)} unique to this process")
                name = proc.name()
                pid = proc.pid
                thread_count = proc.num_threads()
                summary.append(f"Process: name {name}, id {pid}, threads {thread_count}")
                summary.append("")  # blank line
        if isinstance(self.bot, discord.AutoShardedClient):
            mode = "autosharded"
        elif self.bot.shard_count:
            mode = "manually sharded"
        else:
            mode = "unsharded"
        summary.append(f"Bot stats: {mode}, {len(self.bot.commands)} command(s), {len(self.bot.cogs)} cog(s), "
                       f"{len(self.bot.guilds)} guild(s), {len(self.bot.users)} user(s)")
        summary.append(f"Ping: {round(self.bot.latency * 1000, 2)}ms")
        await ctx.send("\n".join(summary))

    @jsk.command(name="py", aliases=["python", "p"])
    async def jsk_python(self, ctx: commands.Context, *, argument: CodeblockConverter = None):
        """
        Direct evaluation of Python code.
        """
        if argument is None:
            keys = self._scope.globals.keys()
            if keys:
                return await ctx.send("Current scope is: " + ", ".join(keys) + ".")
            return await ctx.send("Default scope only.")
        arg_dict = sub_get_var_dict_from_ctx(ctx, self.arg_prefix)
        scope = self.scope
        arg_dict["_"] = self.last_result
        try:
            async with reactor_sub(ctx.message):
                with self.submit(ctx):
                    async for result in AsyncCodeExecutor(argument.content, scope, arg_dict=arg_dict):
                        if result is None:
                            continue
                        self.last_result = result
                        if isinstance(result, discord.File):
                            await ctx.send(file=result)
                        elif isinstance(result, discord.Embed):
                            await ctx.send(embed=result)
                        elif isinstance(result, PaginatorInterface):
                            await result.send_to(ctx)
                        else:
                            if not isinstance(result, str):
                                result = repr(result)
                            if len(result) > 2000:
                                paginator = WrappedPaginator(prefix='```py', suffix='```', max_size=1985)
                                paginator.add_line(result)
                                interface = PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
                                await interface.send_to(ctx)
                            else:
                                if result.strip() == '':
                                    result = "\u200b"
                                await ctx.send(f"```py\n{result.replace(self.bot.http.token, '[token omitted]')}```")
        finally:
            scope.clear_intersection(arg_dict)

def setup(bot):
    bot.add_cog(sub_jsk(bot))
