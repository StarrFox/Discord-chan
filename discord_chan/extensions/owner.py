from io import BytesIO

import aiohttp
import discord
from discord.ext import commands

from discord_chan import DiscordChan, SubContext


class Owner(commands.Cog, name="owner"):
    """
    Owner commands
    """

    def __init__(self, bot: DiscordChan):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context):
        if not await self.bot.is_owner(ctx.author):
            raise commands.NotOwner("You do not own this bot")
        return True

    @commands.command()
    async def enable(self, ctx: SubContext, *, cmd):
        command = self.bot.get_command(cmd)

        if command is None:
            return await ctx.send("Command not found.")

        command.enabled = True
        await ctx.confirm("Command enabled.")

    @commands.command()
    async def disable(self, ctx: SubContext, *, cmd):
        command = self.bot.get_command(cmd)

        if command is None:
            return await ctx.send("Command not found.")

        command.enabled = False
        await ctx.confirm("Command disabled.")

    @commands.command()
    async def resend_file(self, ctx: SubContext, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.read()

        try:
            filename = url.split("/")[-1]
        except IndexError:
            filename = None

        await ctx.send(file=discord.File(BytesIO(data), filename))

    @commands.command()
    async def features(self, ctx: SubContext):
        """
        Show what features are enabled
        """
        guild_features = await self.bot.database.get_all_guild_enabled_features()

        result = ""

        for guild_id in guild_features.keys():
            guild = await self.bot.fetch_guild(guild_id)

            result += f"{guild.name}: {' '.join(guild_features[guild_id])}\n"

        await ctx.send(result or "no enabled features")


async def setup(bot):
    await bot.add_cog(Owner(bot))
