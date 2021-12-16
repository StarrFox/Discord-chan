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
    CodeblockPageSource,
    DCMenuPages,
    FetchedMember,
    FetchedUser,
    SubContext,
    db,
)


def is_above(invoker: discord.Member, user: discord.Member):
    return invoker.top_role > user.top_role


# Todo: add back mod stuff
class Mod(commands.Cog, name="mod"):
    """Moderation commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.guild_only()
    @commands.group(invoke_without_command=True, aliases=["prefixes"])
    async def prefix(self, ctx: commands.Context):
        """
        Base prefix command,
        Lists prefixes
        """
        prefixes = [
            f"{idx}. `{prefix}`"
            for idx, prefix in enumerate(self.bot.prefixes[ctx.guild.id], 1)
        ]

        source = CodeblockPageSource(prefixes, per_page=5)

        menu = DCMenuPages(source)

        await menu.start(ctx)

    @commands.check_any(
        commands.has_permissions(administrator=True),
        commands.has_permissions(manage_messages=True),
    )
    @prefix.command()
    async def add(self, ctx: SubContext, prefix: str):
        """
        Adds a prefix to this guild
        """
        # it should never be over 20 but just to be sure
        if len(self.bot.prefixes[ctx.guild.id]) >= 20:
            return await ctx.send(
                "Guild at max prefixes of 20, remove one to add this one."
            )
        elif prefix in self.bot.prefixes[ctx.guild.id]:
            return await ctx.send("Prefix already added.")

        self.bot.prefixes[ctx.guild.id].add(prefix)
        async with db.get_database() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "INSERT INTO prefixes (guild_id, prefixes) VALUES (?, ?) "
                    "ON CONFLICT (guild_id) DO UPDATE SET prefixes = EXCLUDED.prefixes;",
                    (ctx.guild.id, self.bot.prefixes[ctx.guild.id]),
                )
            await conn.commit()

        await ctx.confirm()

    @commands.check_any(
        commands.has_permissions(administrator=True),
        commands.has_permissions(manage_messages=True),
    )
    @prefix.command(aliases=["rem"])
    async def remove(self, ctx: SubContext, prefix: str):
        """
        Remove a prefix from this guild
        """
        if prefix not in self.bot.prefixes[ctx.guild.id]:
            return await ctx.send("Prefix not in this guild's prefixes.")

        async with db.get_database() as conn:
            async with conn.cursor() as cursor:
                # It's the only one in the guild so just reset to default prefix
                # rather than an empty set
                if len(self.bot.prefixes[ctx.guild.id]) == 1:
                    del self.bot.prefixes[ctx.guild.id]
                    await cursor.execute(
                        "DELETE FROM prefixes WHERE guild_id IS (?)", (ctx.guild.id,)
                    )

                else:
                    self.bot.prefixes[ctx.guild.id].remove(prefix)
                    await cursor.execute(
                        "UPDATE prefixes SET prefixes=? WHERE guild_id IS ?;",
                        (self.bot.prefixes[ctx.guild.id], ctx.guild.id),
                    )
            await conn.commit()

        await ctx.confirm()

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


def setup(bot):
    bot.add_cog(Mod(bot))
