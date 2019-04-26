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
        e = discord.Embed(title="Guild add", color=discord.Color.dark_purple())
        e.set_thumbnail(url=guild.icon_url)
        e.add_field(name="Name:", value=guild.name)
        e.add_field(name="ID:", value=guild.id)
        e.add_field(name="Owner:", value=str(guild.owner))
        e.add_field(name="Member count", value=guild.member_count)
        await self.log_channel.send(embed=e)
        self.bot.logger.info(f"Joined {guild.name}")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        e = discord.Embed(title="Guild remove", color=discord.Color.dark_purple())
        e.set_thumbnail(url=guild.icon_url)
        e.add_field(name="Name:", value=guild.name)
        e.add_field(name="ID:", value=guild.id)
        e.add_field(name="Owner:", value=str(guild.owner))
        e.add_field(name="Member count", value=guild.member_count)
        await self.log_channel.send(embed=e)
        self.bot.logger.info(f"Left {guild.name}")

    #Pm logger
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None and not message.author.bot:
            e = discord.Embed(title=f"Dm from {str(message.author)}", color=discord.Color.dark_purple())
            e.set_thumbnail(url=message.author.avatar_url)
            e.add_field(name="Author ID:", value=message.author.id)
            e.add_field(name="Content:", value=message.content, inline=False)
            await self.log_channel.send(embed=e)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        if ctx.author.id in self.bot.owners:
            return
        g = None
        if ctx.guild:
            g = ctx.guild.id
        log = f"Commandlog path={ctx.command.full_parent_name + ctx.command.name} g/c/u={g}/{ctx.channel.id}/{ctx.author.id}"
        invoke = f"Content={ctx.message.content}"
        if len(log+invoke)+8 >= 2000:
            await self.log_channel.send(utils.block(log))
            await self.log_channel.send(utils.block(invoke))
        else:
            await self.log_channel.send(utils.block(log+invoke))
        self.bot.logs.append(log+invoke)

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
            return await ctx.send("You are missing required permission(s)")
        e = discord.Embed(title="Command error", description=str(error), color=discord.Color.dark_purple())
        e.set_thumbnail(url=ctx.author.avatar_url)
        e.add_field(name="Guild:", value=f"Name: {ctx.guild.name}\nID: {ctx.guild.id}")
        e.add_field(name="Invoker", value=f"Name: {str(ctx.author)}\nID: {ctx.author.id}")
        if len(ctx.message.content) <= 1024:
            e.add_field(name="Content:", value=ctx.message.content)
        await self.log_channel.send(embed=e)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

def setup(bot):
    bot.add_cog(logger(bot))
