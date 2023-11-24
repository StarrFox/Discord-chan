import textwrap

import discord
import pendulum
from discord.ext import commands

from discord_chan import DiscordChan
from discord_chan.context import SubContext
from discord_chan.menus import (
    DCMenuPages,
    EmbedFieldProxy,
    EmbedFieldsPageSource,
    NormalPageSource,
)
from discord_chan.snipe import Snipe as Snipe_obj
from discord_chan.snipe import SnipeMode


class SnipeQueryFlags(commands.FlagConverter, delimiter=" ", prefix="--"):
    channel: discord.TextChannel | None
    mode: SnipeMode | None
    author: discord.Member | None
    contains: str | None


class Snipe(commands.Cog, name="snipe"):
    def __init__(self, bot: DiscordChan):
        self.bot = bot

    @commands.Cog.listener("on_message_delete")
    async def snipe_delete(self, message: discord.Message):
        await self.attempt_add_snipe(message, SnipeMode.edited)

    @commands.Cog.listener("on_bulk_message_delete")
    async def bulk_snipe_delete(self, messages: list[discord.Message]):
        for message in messages:
            await self.attempt_add_snipe(message, SnipeMode.purged)

    @commands.Cog.listener("on_message_edit")
    async def snipe_edit(self, before: discord.Message, after: discord.Message):
        if before.content != after.content:
            await self.attempt_add_snipe(before, SnipeMode.edited)

    async def attempt_add_snipe(self, message: discord.Message, mode: SnipeMode):
        if message.content:
            snipe = Snipe_obj(
                id=message.id,
                mode=mode,
                author=message.author.id,
                content=message.content,
                channel=message.channel.id,
                server=message.guild.id if message.guild is not None else 0,
                time=pendulum.now("UTC"),
            )

            await self.bot.database.add_snipe(snipe)

    @commands.bot_has_permissions(embed_links=True)
    @commands.group(name="snipe", invoke_without_command=True)
    async def snipe_command(
        self,
        ctx: commands.Context,
        index: int = 0,
        *,
        query_flags: SnipeQueryFlags,
    ):
        """
        Snipe for edited/purged/deleted messages

        flags:
            --channel: the channel
            --author: the author
            --mode: the snipe mode (edited/purged/deleted)
        """
        negative = index < 0

        if abs(index) > 10_000_000:
            return await ctx.send(
                f"{index} is over the index cap of (-)10,000,000; do you really have that many snipes?"
            )

        if query_flags.channel is not None:
            if query_flags.channel.nsfw and not getattr(ctx.channel, "nsfw", False):
                raise commands.BadArgument(
                    "Cannot snipe a nsfw channel from a non-nsfw channel"
                )

            snipe_channel = query_flags.channel
        else:
            snipe_channel = ctx.channel

        snipes, snipe_count = await self.bot.database.get_snipes(
            server=ctx.guild.id if ctx.guild else 0,
            channel=snipe_channel.id,
            contains=query_flags.contains,
            limit=abs(index) + 1,
            negative=negative,
            author=query_flags.author.id if query_flags.author else None,
            mode=query_flags.mode,
        )
        # snipe_count is the total snipes returned from the quary and total_snipes is
        # the limit adjusted amount returned
        total_snipes = len(snipes)

        if total_snipes == 0:
            return await ctx.send("No snipes found for this query")

        if negative and abs(index) > (total_snipes + 1):
            return await ctx.send(f"Only {total_snipes} snipes found for this query")
        elif not negative and index > (total_snipes - 1):
            return await ctx.send(f"Only {total_snipes} snipes found for this query")

        if negative:
            target_snipe = snipes[abs(index) - 1]
        else:
            target_snipe = snipes[index]

        if ctx.guild is not None:
            target_author = ctx.guild.get_member(target_snipe.author)
        else:
            target_author = self.bot.get_user(target_snipe.author)

            if target_author is None:
                try:
                    target_author = await self.bot.fetch_user(target_snipe.author)
                except discord.NotFound:
                    target_author = "[User unreadable]"

        embed = discord.Embed(
            title=f"[{target_snipe.mode.name}] {target_author} {target_snipe.discord_timestamp}",
            description=target_snipe.content,
        )

        embed.set_footer(text=f"{index}/{snipe_count - 1}")

        await ctx.send(embed=embed)

    @snipe_command.command(name="list")
    async def snipe_command_list(
        self, ctx: commands.Context, *, query_flags: SnipeQueryFlags
    ):
        """
        List snipes instead of just one
        """
        if query_flags.channel is not None:
            if query_flags.channel.nsfw and not getattr(ctx.channel, "nsfw", False):
                raise commands.BadArgument(
                    "Cannot snipe a nsfw channel from a non-nsfw channel"
                )

            snipe_channel = query_flags.channel
        else:
            snipe_channel = ctx.channel

        snipes, _ = await self.bot.database.get_snipes(
            server=ctx.guild.id if ctx.guild else 0,
            channel=snipe_channel.id,
            contains=query_flags.contains,
            author=query_flags.author.id if query_flags.author else None,
            mode=query_flags.mode,
        )
        total_snipes = len(snipes)

        if total_snipes == 0:
            return await ctx.send("No snipes found for this query")

        field_proxies: list[EmbedFieldProxy] = []

        for snipe in snipes:
            # TODO: add lazy loading of usernames
            if ctx.guild is not None:
                target_author = ctx.guild.get_member(snipe.author)
            else:
                target_author = self.bot.get_user(snipe.author)

            if target_author is None:
                try:
                    target_author = await self.bot.fetch_user(snipe.author)
                except discord.NotFound:
                    target_author = "[User unreadable]"

            # embed field value's max at 1024 characters
            if len(snipe.content) >= 1024:
                content = textwrap.wrap(snipe.content, 1024 - 3)[0] + "..."
            else:
                content = snipe.content

            field_proxies.append(
                EmbedFieldProxy(
                    name=f"[{snipe.mode.name}] {target_author} {snipe.discord_timestamp}",
                    value=content,
                    inline=False,
                )
            )

        source = EmbedFieldsPageSource(field_proxies, per_page=4)
        menu = DCMenuPages(source)

        await menu.start(ctx)

    @snipe_command.command(name="stat")
    @commands.guild_only()
    async def snipe_command_stat(self, ctx: SubContext):
        """
        Get stats on who has the most snipes
        """
        leaderboard = await self.bot.database.get_snipe_leaderboard(ctx.guild.id)

        entries: list[str] = []

        for author_id, count in leaderboard.items():
            author = ctx.guild.get_member(author_id)

            if author is None:
                author = await self.bot.fetch_user(author_id)

            entries.append(f"- {author.display_name}: {count}")

        _, total = await self.bot.database.get_snipes(server=ctx.guild.id)

        entries = [f"total = {total}", ""] + entries

        source = NormalPageSource(entries, per_page=10)
        menu = DCMenuPages(source)

        await menu.start(ctx)


async def setup(bot):
    await bot.add_cog(Snipe(bot))
