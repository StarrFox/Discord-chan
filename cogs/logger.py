import discord
from discord.ext import commands
import asyncio
import traceback
import aiohttp
from os import system
import sys
from extras import utils

class logger(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.log_channel = bot.get_channel(571132727902863376)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        log = f"GuildAddlog name={guild.name} id={guild.id} owner={guild.owner} members={guild.member_count}"
        await utils.paginate(log, self.log_channel)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        log = f"GuildRemlog name={guild.name} id={guild.id} owner={guild.owner} members={guild.member_count}"
        await utils.paginate(log, self.log_channel)

    #Pm logger
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None and not message.author.bot:
            log = f"PMlog author={message.author.id} content={message.content}"
            await utils.paginate(log, self.log_channel)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        if await self.bot.is_owner(ctx.author):
            return
        log = f"Commandlog path={ctx.command.full_parent_name} {ctx.command.name} c/a={ctx.channel.id}/{ctx.author.id} content={ctx.message.content}"
        await utils.paginate(log, self.log_channel)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        error = getattr(error, 'original', error)
        ignored = (commands.CommandNotFound)
        if isinstance(error, ignored):
            return
        elif isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(str(error))
        elif isinstance(error, commands.UserInputError):
            await ctx.send("Command usage error")
            return await ctx.send_help(ctx.command)
        elif isinstance(error, commands.CheckFailure):
            if ctx.author.id == 145897775274524672 and ctx.command.name == "laval":
                return
            return await ctx.send("You are missing required permission(s)")
        trace = traceback.format_exception(type(error), error, error.__traceback__)
        log = f"Errorlog guild={ctx.guild.id} author={ctx.author.id} content={ctx.message.content} traceback=\n{''.join(trace)}"
        await utils.paginate(log, self.log_channel)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

def setup(bot):
    bot.add_cog(logger(bot))
