#  Copyright © 2019 StarrFox
#  #
#  Discord Chan is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  #
#  Discord Chan is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#  #
#  You should have received a copy of the GNU Affero General Public License
#  along with Discord Chan.  If not, see <https://www.gnu.org/licenses/>.

from discord.ext import commands


def is_owner():
    async def predicate(ctx):
        if await ctx.bot.is_owner(ctx.author):
            return True
        raise commands.NotOwner()

    return commands.check(predicate)


def has_permissions(**perms):
    async def predicate(ctx):
        ch = ctx.channel
        permissions = ch.permissions_for(ctx.author)
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm, None) != value]
        if not missing or await ctx.bot.is_owner(ctx.author):
            return True
        raise commands.MissingPermissions(missing)

    return commands.check(predicate)


def guildowner():
    async def predicate(ctx):
        if ctx.guild is None:
            return False
        elif ctx.message.author == ctx.guild.owner:
            return True
        elif await ctx.bot.is_owner(ctx.author):
            return True
        raise commands.MissingPermissions(["Guild owner"])

    return commands.check(predicate)
