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

from extras import checks
from core import DiscordChan
from jishaku.paginators import WrappedPaginator, PaginatorEmbedInterface


def is_above(invoker: discord.Member, user: discord.Member):
    return invoker.top_role > user.top_role


class mod(commands.Cog):
    """Moderation commands"""

    def __init__(self, bot: DiscordChan):
        self.bot = bot

    # TODO: test these
    @commands.group(invoke_without_command=True, aliases=["prefixes"])
    async def prefix(self, ctx: commands.Context):
        """
        Base prefix command
        Lists prefixes
        """
        prefixes = '\n'.join(self.bot.prefixes[ctx.guild.id])

        paginator = WrappedPaginator(max_size=500)

        paginator.add_line(prefixes)

        interface = PaginatorEmbedInterface(self.bot, paginator, owner=ctx.author)

        await interface.send_to(ctx)

    @prefix.command()
    @checks.has_permissions(administrator=True)
    async def add(self, ctx: commands.Context, prefix: str):
        """
        Adds a prefix to the guild
        """
        # it should never be over 20 but just to be sure
        if len(self.bot.prefixes[ctx.guild.id]) >= 20:
            return await ctx.send('Guild at max prefixes of 20, remove one to add this one.')

        # maybe I should tell them if it was already in there?
        self.bot.prefixes[ctx.guild.id].add(prefix)
        await ctx.send('Added.')

    @prefix.command(aliases=['rem'])
    @checks.has_permissions(administrator=True)
    async def remove(self, ctx: commands.Context, prefix: str):
        """Remove a prefix for this server"""
        if prefix in self.bot.prefixes[ctx.guild.id]:
            # It's the only one in the guild so just reset to default prefix
            # rather than an empty set
            if len(self.bot.prefixes[ctx.guild.id]) == 1:
                del self.bot.prefixes[ctx.guild.id]

            else:
                self.bot.prefixes[ctx.guild.id].remove(prefix)

            await ctx.send('Prefix removed')
        else:
            await ctx.send("Prefix not in this guild's prefixes")

    # Todo: test this
    @commands.command()
    @commands.bot_has_permissions(manage_messages=True)
    @checks.has_permissions(manage_messages=True)
    async def purge(self,
                    ctx: commands.Context,
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

    @commands.command()
    @commands.bot_has_permissions(ban_members=True)
    @checks.has_permissions(ban_members=True)
    async def hackban(self, ctx: commands.Context, member_id: int, *, reason=None):
        """
        Bans using an id
        """
        await ctx.guild.ban(discord.Object(id=member_id), reason=reason)
        await ctx.send(f"Banned {member_id}")

def setup(bot):
    bot.add_cog(mod(bot))
