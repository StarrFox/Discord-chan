from typing import Annotated

import discord
from discord.ext import commands

from discord_chan import DiscordChan, FetchedUser, SubContext


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
    async def dm(
        self, ctx: SubContext, user: Annotated[discord.User, FetchedUser], *, msg: str
    ):
        await user.send(msg)
        await ctx.confirm("Message sent.")

    @commands.command(aliases=["off", "restart"])
    async def shutdown(self, ctx: SubContext):
        await ctx.confirm("Logging out....")
        await self.bot.close()

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


async def setup(bot):
    await bot.add_cog(Owner(bot))
