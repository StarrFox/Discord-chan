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

from discord.ext import commands

from discord_chan import (
    DiscordChan,
    FetchedUser,
    SubContext,
)


class Owner(commands.Cog, name="owner"):
    """
    Owner commands
    """

    def __init__(self, bot: DiscordChan):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context):
        if not await self.bot.is_owner(ctx.author):
            raise commands.NotOwner("You do not own this bot.")
        return True

    @commands.command()
    async def dm(self, ctx: SubContext, user: FetchedUser, *, msg: str):
        await user.send(msg)
        await ctx.confirm("Message sent.")

    @commands.command(aliases=["off", "restart"])
    async def shutdown(self, ctx: SubContext):
        await ctx.confirm("Logging out....")
        await self.bot.logout()

    @commands.command()
    async def enable(self, ctx: SubContext, *, cmd):
        command = self.bot.get_command(cmd)

        if command is None:
            return await ctx.send("Command not found.")

        command.enabled = True

        await ctx.confirm("Command enabled.")

    @commands.command()
    async def disable(self, ctx: SubContext, *, cmd):
        command = self.bot.get_command(cmd)

        if command is None:
            return await ctx.send("Command not found.")

        command.enabled = False

        await ctx.confirm("Command disabled.")

    @commands.command(hidden=True)
    async def loadjsk(self, ctx: SubContext):
        """
        Backup command to load jishaku
        """
        await self.bot.load_extension("jishaku")
        await ctx.confirm("Jishaku loaded.")


async def setup(bot):
    await bot.add_cog(Owner(bot))
