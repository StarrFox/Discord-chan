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
task = "thonk:536720018545573928"
done = "glowcheck:536720140025200641"
syntax_error = "glowanix:536720254022320167"
timeout_error = "error:539157627385413633"
error = "glowanix:536720254022320167"

def sub_get_var_dict_from_ctx(ctx):
    return {
        '_author': ctx.author,
        '_bot': ctx.bot,
        '_channel': ctx.channel,
        '_ctx': ctx,
        '_guild': ctx.guild,
        '_message': ctx.message,
        '_msg': ctx.message,
        '_get': discord.utils.get
    }

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
        cache_summary = f""
        if isinstance(self.bot, discord.AutoShardedClient):
            summary.append(f"Mode: autosharded")
        elif self.bot.shard_count:
            summary.append(f"Mode: manually sharded")
        else:
            summary.append(f"Mode: unsharded")
        summary.append(f"Bot stats: {len(self.bot.commands)} command(s), {len(self.bot.cogs)} cog(s), "
                       f"{len(self.bot.guilds)} guild(s), {len(self.bot.users)} user(s)")
        summary.append(f"Ping: {round(self.bot.latency * 1000, 2)}ms")
        await ctx.send("\n".join(summary))

    @jsk.group(name="retain", invoke_without_command=True, ignore_extra=False)
    async def jsk_retain(self, ctx, *, toggle: bool = None):
        """
        Turn variable retention for REPL on or off.
        Provide no argument for current status.
        """
        if toggle is None:
            if self.retain:
                return await ctx.send("Variable retention is set to ON.")
            return await ctx.send("Variable retention is set to OFF.")
        if toggle:
            if self.retain:
                return await ctx.send("Variable retention is already set to ON.")
            self.retain = True
            self._scope = Scope()
            return await ctx.send("Variable retention is ON. Future REPL sessions will retain their scope.")
        if not self.retain:
            return await ctx.send("Variable retention is already set to OFF.")
        self.retain = False
        return await ctx.send("Variable retention is OFF. Future REPL sessions will dispose their scope when done.")

    @jsk_retain.command(name="reset", aliases=["r"])
    async def jsk_retain_reset(self, ctx):
        """
        Resets the current scope
        if there is one
        """
        if not self.retain:
            return await ctx.send("Variable retention must be set to ON to reset.")
        self._scope = Scope()
        await ctx.send("Scope has been reset.")

    @jsk.command(name="py", aliases=["python"])
    async def jsk_python(self, ctx: commands.Context, *, argument: CodeblockConverter):
        """
        Direct evaluation of Python code.
        """
        arg_dict = sub_get_var_dict_from_ctx(ctx)
        scope = self.scope
        scope.clean()
        arg_dict["_"] = self.last_result
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
                            # repr all non-strings
                            result = repr(result)
                        if len(result) > 2000:
                            # inconsistency here, results get wrapped in codeblocks when they are too large
                            #  but don't if they're not. probably not that bad, but noting for later review
                            paginator = WrappedPaginator(prefix='```py', suffix='```', max_size=1985)
                            paginator.add_line(result)
                            interface = PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
                            await interface.send_to(ctx)
                        else:
                            if result.strip() == '':
                                result = "\u200b"
                            await ctx.send(result.replace(self.bot.http.token, "[token omitted]"))

def setup(bot):
    bot.add_cog(sub_jsk(bot))
