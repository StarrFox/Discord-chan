import random
from datetime import timedelta
from venv import logger

import discord
from discord.ext import commands
from loguru import logger

from discord_chan import (
    DiscordChan,
    SubContext,
)


GLORPY_ID = 1330327277589758076


class Glorpies(commands.Cog, name="glorpies"):
    """Glerp"""

    def __init__(self, bot: DiscordChan):
        self.bot = bot

        self.landmine_rarity = 20

    async def cog_check(self, ctx: commands.Context) -> bool:  # type: ignore (this method is allowed to be sync and async)
        if ctx.guild is None:
            raise commands.NoPrivateMessage()

        if not ctx.guild.id == GLORPY_ID:
            raise commands.CheckFailure("not glorpy enough")

        return True

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.guild.id != GLORPY_ID:
            return

        should_time = random.randrange(0, self.landmine_rarity) == 1

        if should_time:
            if not isinstance(message.author, discord.Member):
                logger.warning("Guild member cache polluted")
                return

            if not message.channel.permissions_for(message.guild.me).moderate_members:
                logger.info("Missing permission to timeout members in glorp server")
                return

            await message.author.timeout(timedelta(minutes=10), reason="sus")
            await message.channel.send(
                f"\N{COLLISION SYMBOL} {message.author.mention} stepped on a landmine and has been timed out for 10 years!"
            )

            # progressively more rare
            self.landmine_rarity += 10

    @commands.command(name="rename")
    async def rename_command(
        self,
        ctx: SubContext,
        target: discord.Member,
        *,
        new_name: str | None = commands.parameter(
            default=None, description="New nickname, don't provide to reset"
        ),
    ):
        """
        Rename another member
        """
        if new_name is not None:
            name_len = len(new_name)

            if name_len > 32:
                return await ctx.send(
                    f"Name must be 32 or less characters long, provided was {name_len}"
                )

        try:
            await target.edit(nick=new_name)
            await ctx.confirm("Renamed")
        except discord.Forbidden:
            if ctx.guild.owner is None:
                return await ctx.deny("Couldn't rename them")

            if target.id == ctx.guild.owner.id:
                await ctx.send(
                    f"{target.mention} rename yourself :3",
                    allowed_mentions=discord.AllowedMentions(users=[target]),
                )

            return await ctx.deny("Couldn't rename them")


async def setup(bot):
    await bot.add_cog(Glorpies(bot))
