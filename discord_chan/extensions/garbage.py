import re
import contextlib

import discord
from discord.ext import commands

import discord_chan


loli_filter = re.compile(r"\?tags=(\w|\+)*loli([^a-zA-Z]|$)?")


class Garbage(commands.Cog):
    def __init__(self, bot: discord_chan.DiscordChan) -> None:
        super().__init__()
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def block_olaf_lolis(self, message: discord.Message):
        if message.guild is None:
            return

        # wizspoil
        if message.guild.id != 1015677559020724264:
            return

        # anti-olaf
        if len(list(loli_filter.finditer(message.content))) > 0:
            return await message.delete()

    @commands.group(invoke_without_command=True, aliases=["mc"])
    @discord_chan.checks.some_guilds(1015677559020724264)  # spoil server only
    async def minecraft(self, ctx: discord_chan.SubContext, username: str):
        """
        Set your minecraft username
        """
        await ctx.bot.database.update_minecraft_username(
            user_id=ctx.author.id, username=username
        )
        await ctx.confirm("Username updated")

        mc_role = ctx.guild.get_role(1241826442501947543)

        if mc_role is None:
            return

        with contextlib.suppress(discord.Forbidden):
            await ctx.author.add_roles(mc_role, reason="minecraft")

    @minecraft.command(name="list")
    async def minecraft_list(self, ctx: discord_chan.SubContext):
        """
        Get minecraft usernames
        """
        usernames = await ctx.bot.database.get_minecraft_usernames()

        result = ""
        for user_id, name in usernames.items():
            member_name = await ctx.bot.get_member_reference(ctx, user_id)
            result += f"{member_name}: {name}"

        if result == "":
            result = "No usernames stored"

        await ctx.send(result)


async def setup(bot: discord_chan.DiscordChan):
    await bot.add_cog(Garbage(bot))
