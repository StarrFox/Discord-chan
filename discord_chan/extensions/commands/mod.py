# -*- coding: utf-8 -*-
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

import discord
from discord.ext import commands

from discord_chan import db, PartitionPaginator, DCMenuPages, NormalPageSource, SubContext


def is_above(invoker: discord.Member, user: discord.Member):
    return invoker.top_role > user.top_role


# Todo: merge this into general?
class Mod(commands.Cog, name='mod'):
    """Moderation commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Todo: test
    @commands.group(invoke_without_command=True, aliases=["prefixes"])
    async def prefix(self, ctx: SubContext):
        """
        Base prefix command
        Lists prefixes
        """
        prefixes = '\n'.join(
            [f"{idx}. `{prefix}`" for idx, prefix in enumerate(self.bot.prefixes[ctx.guild.id], 1)]
        )

        paginator = PartitionPaginator(max_size=100)

        paginator.add_line(prefixes)

        source = NormalPageSource(paginator.pages)

        menu = DCMenuPages(source)

        await menu.start(ctx)

    @commands.has_permissions(administrator=True)
    @prefix.command()
    async def add(self, ctx: SubContext, prefix: str):
        """
        Adds a prefix to this guild
        """
        # it should never be over 20 but just to be sure
        if len(self.bot.prefixes[ctx.guild.id]) >= 20:
            return await ctx.send('Guild at max prefixes of 20, remove one to add this one.')
        elif prefix in self.bot.prefixes[ctx.guild.id]:
            return await ctx.send('Prefix already added.')

        self.bot.prefixes[ctx.guild.id].add(prefix)
        async with db.get_database() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("INSERT INTO prefixes (guild_id, prefixes) VALUES (?, ?) "
                                     "ON CONFLICT (guild_id) DO UPDATE SET prefixes = EXCLUDED.prefixes;",
                                     (ctx.guild.id, self.bot.prefixes[ctx.guild.id])
                                     )
            await conn.commit()

        await ctx.confirm()

    @commands.has_permissions(administrator=True)
    @prefix.command(aliases=['rem'])
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
                    await cursor.execute("DELETE FROM prefixes WHERE guild_id IS (?)", (ctx.guild.id,))

                else:
                    self.bot.prefixes[ctx.guild.id].remove(prefix)
                    await cursor.execute("UPDATE prefixes SET prefixes=? WHERE guild_id IS ?;",
                                         (self.bot.prefixes[ctx.guild.id], ctx.guild.id))
            await conn.commit()

        await ctx.confirm()

    @commands.bot_has_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    @commands.command()
    async def purge(self,
                    ctx: SubContext,
                    number: int,
                    user: typing.Optional[discord.Member] = None,
                    *, text: str = None):
        """
        Purges messages from certain user or certain text
        """
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
        await ctx.send(f'Deleted {len(deleted)} message(s)', delete_after=5)

    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    @commands.command()
    async def hackban(self, ctx: SubContext, member_id: int, *, reason=None):
        """
        Bans using an id
        """
        await ctx.guild.ban(discord.Object(id=member_id), reason=reason)
        await ctx.confirm()


def setup(bot):
    bot.add_cog(Mod(bot))
