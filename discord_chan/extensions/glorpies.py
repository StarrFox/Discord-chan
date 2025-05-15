import discord
from discord.ext import commands

from discord_chan import (
    DiscordChan,
    SubContext,
)


GLORPY_ID = 1330327277589758076


class Glorpies(commands.Cog, name="glorpies"):
    """Glerp"""

    def __init__(self, bot: DiscordChan):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:  # type: ignore (this method is allowed to be sync and async)
        if ctx.guild is None:
            raise commands.NoPrivateMessage()

        if not ctx.guild.id == GLORPY_ID:
            raise commands.CheckFailure("not glorpy enough")

        return True

    @commands.command(name="rename")
    async def rename_command(self, ctx: SubContext, target: discord.Member, *, new_name: str | None = commands.parameter(default=None, description="New nickname, don't provide to reset")):
        """
        Rename another member
        """
        if new_name is not None:
            name_len = len(new_name)

            if name_len > 32:
                return await ctx.send(f"Name must be 32 or less characters long, provided was {name_len}")

        try:
            await target.edit(nick=new_name)
            await ctx.confirm("Renamed")
        except discord.Forbidden:
            if ctx.guild.owner is None:
                return await ctx.deny("Couldn't rename them")

            if target.id == ctx.guild.owner.id:
                await ctx.send(f"{target.mention} rename yourself :3", allowed_mentions=discord.AllowedMentions(users=[target]))
            
            return await ctx.deny("Couldn't rename them")


async def setup(bot):
    await bot.add_cog(Glorpies(bot))
