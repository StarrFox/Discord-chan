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


def is_above(invoker: discord.Member, user: discord.Member):
    return invoker.top_role > user.top_role


class mod(commands.Cog):
    """Moderation commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, aliases=["prefixes"])
    async def prefix(self, ctx: commands.Context):
        """List and add/remove your prefixes"""
        guild = ctx.guild
        if guild.id in self.bot.prefixes:
            e = discord.Embed(
                description="\n".join(self.bot.prefixes[guild.id]),
                color=discord.Color.blurple()
            )
            await ctx.send(embed=e)
        else:
            await ctx.send('exe!')

    @prefix.command()
    @checks.has_permissions(administrator=True)
    async def add(self, ctx: commands.Context, *, prefix: str):
        """Add a prefix for this server"""
        guild = ctx.guild
        prefix = prefix.replace("\N{QUOTATION MARK}", "")
        if guild.id in self.bot.prefixes:
            if prefix in self.bot.prefixes[guild.id]:
                return await ctx.send("Prefix already added")
            if len(self.bot.prefixes[guild.id]) >= 20:
                return await ctx.send('Can only have 20 prefixes, remove one to add this one')
            else:
                self.bot.prefixes[guild.id].append(prefix)
                await ctx.send("Prefix added")
        else:
            self.bot.prefixes[guild.id] = []
            self.bot.prefixes[guild.id].append(prefix)
            await ctx.send("Prefix added")

    @prefix.command(aliases=['rem'])
    @checks.has_permissions(administrator=True)
    async def remove(self, ctx: commands.Context, *, prefix: str):
        """Remove a prefix for this server"""
        guild = ctx.guild
        prefix = prefix.replace("\N{QUOTATION MARK}", "")
        if guild.id in self.bot.prefixes:
            if len(self.bot.prefixes[guild.id]) == 1:
                return await ctx.send("Sorry I can't have no prefix")
            else:
                if prefix in self.bot.prefixes[guild.id]:
                    self.bot.prefixes[guild.id].remove(prefix)
                    return await ctx.send("Prefix removed")
                else:
                    return await ctx.send("Prefix not found")
        else:
            await ctx.send("Don't know how you got here lol")

    @commands.command()
    @commands.bot_has_permissions(manage_messages=True)
    @checks.has_permissions(manage_messages=True)
    async def purge(self,
                    ctx: commands.Context,
                    number: int, user: typing.Optional[discord.Member] = None,
                    *, text: str = None):
        """Purges messages from certain user or certain text"""
        channel = ctx.message.channel
        await ctx.message.delete()
        if not user and not text:
            deleted = await channel.purge(limit=number)
        else:
            def msgcheck(msg):
                if user and text:
                    if text in msg.content.lower() and msg.author == user:
                        return True
                    else:
                        return False
                if user:
                    if msg.author == user:
                        return True
                if text:
                    if text in msg.content.lower():
                        return True

            deleted = await channel.purge(limit=number, check=msgcheck)
        await channel.send(f'Deleted {len(deleted)} message(s)', delete_after=5)

    @commands.command()
    @commands.bot_has_permissions(ban_members=True)
    @checks.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason=None):
        """
        Bans a member
        """
        if not is_above(ctx.author, member) and not ctx.guild.owner == ctx.author:
            return await ctx.send("You have to have a higher role to ban someone")
        await member.ban(reason=reason)
        await ctx.send(f"{member.name} was banned")

    @commands.command()
    @commands.bot_has_permissions(ban_members=True)
    @checks.has_permissions(ban_members=True)
    async def hackban(self, ctx: commands.Context, member_id: int, *, reason=None):
        """
        Bans using an id
        """
        await ctx.guild.ban(discord.Object(id=member_id), reason=reason)
        await ctx.send(f"Banned {member_id}")

    @commands.command()
    @commands.bot_has_permissions(kick_members=True)
    @checks.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason=None):
        """
        Kicks a member
        """
        if not is_above(ctx.author, member) and not ctx.guild.owner == ctx.author:
            return await ctx.send("You have to have a higher role to kick someone")
        await member.kick(reason=reason)
        await ctx.send(f"{member.name} has been kicked")

    @commands.command(aliases=["cr"])
    @checks.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def createrole(self, ctx: commands.Context, name: str):
        """
        Creates a role with a given name
        """
        role = await ctx.guild.create_role(name=name)
        await ctx.send(f"Created {role.name}")

def setup(bot):
    bot.add_cog(mod(bot))
