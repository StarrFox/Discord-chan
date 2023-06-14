import typing
from contextlib import suppress

import discord
from discord.ext import commands

from discord_chan import BetweenConverter, FetchedMember, SubContext


def is_above(invoker: discord.Member, user: discord.Member):
    return invoker.top_role > user.top_role


# Todo: add back mod stuff
class Mod(commands.Cog, name="mod"):
    """Moderation commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.command()
    @commands.bot_has_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge(
        self,
        ctx: SubContext,
        number: typing.Annotated[int, BetweenConverter(0, 1000)],
        user: typing.Optional[FetchedMember] = None,
        *,
        text: typing.Optional[str] = None,
    ):
        """
        Purges messages from certain user and/or (with) certain text
        <number> must be between 0 and 1000
        """
        with suppress(discord.Forbidden, discord.NotFound):
            await ctx.message.delete()

        def msgcheck(msg):
            if user and text:
                # Using lower might be inconsistent
                return text in msg.content.lower() and user == msg.author

            elif user:
                return user == msg.author

            elif text:
                return text in msg.content.lower()

            else:
                return True

        # these are the only places the command can be invoked from
        assert isinstance(ctx.channel, discord.abc.Messageable) and isinstance(ctx.channel, discord.abc.GuildChannel)
        deleted = await ctx.channel.purge(limit=number, check=msgcheck)
        with suppress(discord.Forbidden, discord.NotFound):
            await ctx.send(f"Deleted {len(deleted)} message(s)", delete_after=5)

    @commands.command()
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def hackban(self, ctx: SubContext, member_id: int, *, reason=None):
        """
        Bans using an id, must not be a current member
        """
        # guild_only ensures this
        assert ctx.guild is not None
        try:
            await ctx.guild.fetch_member(member_id)
        except (discord.Forbidden, discord.HTTPException):
            await ctx.guild.ban(discord.Object(id=member_id), reason=reason)
            return await ctx.confirm("Id hackbanned.")

        await ctx.send("Member is currently in this guild.")


async def setup(bot):
    await bot.add_cog(Mod(bot))
