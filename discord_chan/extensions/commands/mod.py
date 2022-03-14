#  Copyright © 2019 StarrFox
#
#  Discord Chan is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Discord Chan is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with Discord Chan.  If not, see <https://www.gnu.org/licenses/>.

import typing
from contextlib import suppress

import discord
from discord.ext import commands

from discord_chan import (
    BetweenConverter,
    FetchedMember,
    FetchedUser,
    SubContext,
)


def is_above(invoker: discord.Member, user: discord.Member):
    return invoker.top_role > user.top_role


# Todo: add back mod stuff
class Mod(commands.Cog, name="mod"):
    """Moderation commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.bot_has_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    @commands.command()
    async def purge(
        self,
        ctx: SubContext,
        number: BetweenConverter(0, 1000),
        user: typing.Optional[FetchedMember] = None,
        *,
        text: str = None,
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

        deleted = await ctx.channel.purge(limit=number, check=msgcheck)
        with suppress(discord.Forbidden, discord.NotFound):
            await ctx.send(f"Deleted {len(deleted)} message(s)", delete_after=5)

    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    @commands.command()
    async def hackban(self, ctx: SubContext, member_id: int, *, reason=None):
        """
        Bans using an id, must not be a current member
        """
        try:
            await ctx.guild.fetch_member(member_id)
        except (discord.Forbidden, discord.HTTPException):
            await ctx.guild.ban(discord.Object(id=member_id), reason=reason)
            return await ctx.confirm("Id hackbanned.")

        await ctx.send("Member is currently in this guild.")

    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    @commands.command(aliases=["rp"])
    async def rolepersist(
        self,
        ctx: SubContext,
        role: discord.Role,
        member: typing.Union[FetchedUser, int],
    ):
        if not isinstance(member, int):
            member = member.id

        self.bot.role_persist[ctx.guild.id][member].add(role.id)
        await ctx.confirm("Added")

    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    @commands.command(aliases=["rrp"])
    async def removerolepersist(
        self,
        ctx: SubContext,
        role: discord.Role,
        member: typing.Union[FetchedUser, int],
    ):
        if not isinstance(member, int):
            member = member.id

        self.bot.role_persist[ctx.guild.id][member].discard(role.id)
        await ctx.confirm("Removed")


async def setup(bot):
    await bot.add_cog(Mod(bot))
