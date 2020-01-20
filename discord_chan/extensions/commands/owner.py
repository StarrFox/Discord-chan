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

import discord
from discord.ext import commands

bool_dict = {
    "true": True,
    "on": True,
    "1": True,
    "false": False,
    "off": False,
    "0": False
}

class Owner(commands.Cog, name='owner'):
    """
    Owner commands
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context):
        if not await self.bot.is_owner(ctx.author):
            raise commands.NotOwner('You do not own this bot.')
        return True

    @commands.command()
    async def dm(self, ctx: commands.Context, user: discord.User, *, msg: str):
        await user.send(msg)
        await ctx.send("Message sent.")

    @commands.command(aliases=['off', 'restart'])
    async def shutdown(self, ctx: commands.Context):
        await ctx.send("Shuting down.")
        await self.bot.logout()

    @commands.command()
    async def enable(self, ctx: commands.Context, cmd):
        command = self.bot.get_command(cmd)

        if command is None:
            return await ctx.send('Command not found.')

        command.enabled = True
        await ctx.send('Command enabled.')

    @commands.command()
    async def disable(self, ctx: commands.Context, cmd):
        command = self.bot.get_command(cmd)

        if command is None:
            return await ctx.send('Command not found.')

        command.enabled = False
        await ctx.send('Command disabled.')

    @commands.command(hidden=True)
    async def loadjsk(self, ctx: commands.Context):
        """
        Backup command to load jishaku
        """
        self.bot.load_extension('jishaku')
        await ctx.send('Loaded jishaku.')

def setup(bot):
    bot.add_cog(Owner(bot))
