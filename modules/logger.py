import discord
from discord.ext import commands
import asyncio
import traceback
import aiohttp
from os import system
import sys

class logger:

    def __init__(self, bot):
        self.bot = bot
        self.guild_logs = self.bot.get_channel(527440788934754314)
        self.pm_logs = self.bot.get_channel(521116687437791233)
        self.command_logs = self.bot.get_channel(538653229639270410)
        self.error_logs = self.bot.get_channel(531497184781139968)

    async def on_guild_join(self, guild):
        e = discord.Embed(title="Guild add", color=discord.Color.dark_purple())
        e.set_thumbnail(url=guild.icon_url)
        e.add_field(name="Name:", value=guild.name)
        e.add_field(name="ID:", value=guild.id)
        e.add_field(name="Owner:", value=str(guild.owner))
        e.add_field(name="Member count", value=guild.member_count)
        await self.guild_logs.send(embed=e)
        self.bot.logger.info(f"Joined {guild.name}")

    async def on_guild_remove(self, guild):
        e = discord.Embed(title="Guild remove", color=discord.Color.dark_purple())
        e.set_thumbnail(url=guild.icon_url)
        e.add_field(name="Name:", value=guild.name)
        e.add_field(name="ID:", value=guild.id)
        e.add_field(name="Owner:", value=str(guild.owner))
        e.add_field(name="Member count", value=guild.member_count)
        await self.guild_logs.send(embed=e)
        self.bot.logger.info(f"Left {guild.name}")

    async def on_message(self, message):
        if message.guild is None and not message.author.bot:
            e = discord.Embed(title=f"Dm from {str(message.author)}", color=discord.Color.dark_purple())
            e.set_thumbnail(url=message.author.avatar_url)
            e.add_field(name="Author ID:", value=message.author.id)
            e.add_field(name="Content:", value=message.content, inline=False)
            await self.pm_logs.send(embed=e)

    async def on_command_completion(self, ctx):
        if ctx.author.id in self.bot.owners:
            return
        e = discord.Embed(title=f"Command run log", color=discord.Color.dark_purple())
        e.set_thumbnail(url=ctx.author.avatar_url)
        e.add_field(name="Guild:", value=f"Name: {ctx.guild.name}\nID: {ctx.guild.id}")
        e.add_field(name="Invoker", value=f"Name: {str(ctx.author)}\nID: {ctx.author.id}")
        e.add_field(name="Content:", value=ctx.message.content)
        try:
            await self.command_logs.send(embed=e)
        except Exception as exe:
            await self.command_logs.send("Error in command_complete")
            await self.error_logs.send(exe)

    async def on_command_error(self, ctx, error):
        error = getattr(error, 'original', error)
        ignored = (commands.CommandNotFound, commands.UserInputError, commands.CheckFailure)
        if isinstance(error, ignored):
            return
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(str(error))
        e = discord.Embed(title="Command error", description=str(error), color=discord.Color.dark_purple())
        e.set_thumbnail(url=ctx.author.avatar_url)
        e.add_field(name="Guild:", value=f"Name: {ctx.guild.name}\nID: {ctx.guild.id}")
        e.add_field(name="Invoker", value=f"Name: {str(ctx.author)}\nID: {ctx.author.id}")
        if len(ctx.message.content) <= 1024:
            e.add_field(name="Content:", value=ctx.message.content)
        await self.error_logs.send(embed=e)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

def setup(bot):
    bot.add_cog(logger(bot))