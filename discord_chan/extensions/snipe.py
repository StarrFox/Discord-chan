from typing import Optional

import discord
import pendulum
from discord.ext import commands

from discord_chan import DiscordChan
from discord_chan.menus import DCMenuPages, EmbedFieldProxy, EmbedFieldsPageSource
from discord_chan.snipe import Snipe as Snipe_obj
from discord_chan.snipe import SnipeMode


class SnipeQueryFlags(commands.FlagConverter, delimiter=" ", prefix="--"):
    channel: Optional[discord.TextChannel]
    mode: Optional[SnipeMode]
    author: Optional[discord.Member]
    contains: Optional[str]


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
        index: Optional[int] = 0,
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
        # the Optional on index is just so discord.py allows invocation like `dc/snipe --mode edited`
        assert index is not None

        negative = index < 0

        if abs(index) > 10_000_000:
            return await ctx.send(
                f"{index} is over the index cap of (-)10,000,000; do you really have that many snipes?"
            )

        if query_flags.channel is not None:
            assert isinstance(ctx.channel, discord.TextChannel)

            if query_flags.channel.nsfw and not ctx.channel.nsfw:
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
            return await ctx.send("0 Snipes found for this query")

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
        if query_flags.channel is not None:
            assert isinstance(ctx.channel, discord.TextChannel)

            if query_flags.channel.nsfw and not ctx.channel.nsfw:
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
            author=query_flags.author.id if query_flags.author else None,
            mode=query_flags.mode,
        )
        total_snipes = len(snipes)

        if total_snipes == 0:
            return await ctx.send("0 Snipes found for this query")

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

            field_proxies.append(
                EmbedFieldProxy(
                    name=f"[{snipe.mode.name}] {target_author} {snipe.discord_timestamp}",
                    value=snipe.content,
                    inline=False,
                )
            )

        source = EmbedFieldsPageSource(field_proxies, per_page=4)
        menu = DCMenuPages(source)

        await menu.start(ctx)


async def setup(bot):
    await bot.add_cog(Snipe(bot))
