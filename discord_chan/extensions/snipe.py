import typing
from textwrap import shorten

import discord
from discord.ext import commands

from discord_chan import (
    DCMenuPages,
    DiscordChan,
    EmbedFieldProxy,
    EmbedFieldsPageSource,
    database,
)


class Snipe(commands.Cog, name="snipe"):
    def __init__(self, bot: DiscordChan):
        self.bot = bot

    @commands.Cog.listener("on_message_delete")
    async def snipe_delete(self, message: discord.Message):
        self.attempt_add_snipe(message, "deleted")

    @commands.Cog.listener("on_bulk_message_delete")
    async def bulk_snipe_delete(self, messages: list[discord.Message]):
        for message in messages:
            self.attempt_add_snipe(message, "purged")

    @commands.Cog.listener("on_message_edit")
    async def snipe_edit(self, before: discord.Message, after: discord.Message):
        if before.content != after.content:
            self.attempt_add_snipe(before, "edited")

    @staticmethod
    def attempt_add_snipe(message: discord.Message, mode: str):
        if mode not in ("edited", "purged", "deleted"):
            raise ValueError(f"{mode} is not a valid snipe mode.")

        if message.content:
            snipe = database.Snipe(
                id=message.id,
                mode=mode,
                author=message.author.id,
                content=message.content,
                channel=message.channel.id,
                server=message.guild.id,
            )

            database.add_snipe(snipe)

    @commands.bot_has_permissions(embed_links=True)
    @commands.group(name="snipe", invoke_without_command=True)
    async def snipe_command(self, ctx: commands.Context, index: int = 0):
        snipes = database.get_snipes(server_id=ctx.guild.id, channel=ctx.channel.id)
        total_snipes = len(snipes)
        # they are ordered by creation time

        if index > total_snipes - 1:
            return await ctx.send(f"There are only {total_snipes} in this channel")

        target_snipe = snipes[index]
        target_author = ctx.guild.get_member(target_snipe.author)

        embed = discord.Embed(
            title=f"[{target_snipe.mode}] {target_author} {target_snipe.readable_time}",
            description=target_snipe.content,
        )

        embed.set_footer(text=f"{index}/{total_snipes - 1}")

        await ctx.send(embed=embed)

    # return as list
    @snipe_command.command(name="channel")
    async def snipe_channel(self, ctx: commands.Context, channel: discord.TextChannel = commands.CurrentChannel):
        pass

    # @commands.bot_has_permissions(embed_links=True)
    # @snipe_parser
    # @commands.command(cls=flags.FlagCommand, name="snipe")
    # async def snipe_command(self, ctx: commands.Context, **options: dict):
    #     """
    #     Snipe delete/edited messages from your server.
    #
    #     Optional:
    #     --authors: List of members that authored the snipe
    #     --channel: Channel to snipe from
    #     --server: Snipe from the entire server instead of just a channel
    #     --before: Message id that snipes must be before
    #     --after: Message id that snipes must be after
    #     --list: Show all snipes found instead of one
    #     --mode: Mode of the snipes (edited, deleted, purged)
    #     --contains: String that must be in the snipes
    #
    #     Positional:
    #     index: Index to show from returned snipes, defaults to 0
    #
    #     Nsfw (if not used from one) and channels you can't view are auto filtered out.
    #     """
    #     if options["channel"] is None:
    #         channel = ctx.channel
    #     else:
    #         channel = options["channel"]
    #
    #     # These are filtered out by get_snipes anyway
    #     if not ctx.channel.is_nsfw() and channel.is_nsfw():
    #         return await ctx.send(
    #             "You cannot snipe a nsfw channel from a non-nsfw channel."
    #         )
    #
    #     if isinstance(ctx.author, discord.User):
    #         author = await ctx.guild.fetch_member(ctx.author.id)
    #     else:
    #         author = ctx.author
    #
    #     if not channel.permissions_for(author).read_messages:
    #         return await ctx.send(
    #             "You need permission to view a channel to snipe from it."
    #         )
    #
    #     # noinspection PyTypeChecker
    #     snipes = self.get_snipes(
    #         command_author=author,
    #         command_channel=ctx.channel,
    #         channel=channel,
    #         guild=options["guild"],
    #         authors=options["authors"],
    #         before=options["before"],
    #         after=options["after"],
    #         mode=SnipeMode[options["mode"]] if options["mode"] else None,
    #         contains=options["contains"],
    #     )
    #
    #     if not snipes:
    #         return await ctx.send("No snipes found for this search.")
    #
    #     if options["list"]:
    #         proxies = self.get_proxy_fields(snipes)
    #
    #         # 5 * 1,024 = 5,120 + 500 (names) = 5,620 < 6000 (max embed size)
    #         source = EmbedFieldsPageSource(proxies, per_page=5)
    #
    #         menu = DCMenuPages(source)
    #
    #         await menu.start(ctx)
    #
    #     else:
    #         try:
    #             # noinspection PyTypeChecker
    #             snipe = snipes[options["index"]]
    #         except IndexError:
    #             return await ctx.send("Index out of bounds.")
    #
    #         e = discord.Embed(title=str(snipe), description=snipe.content)
    #
    #         e.set_footer(text=f"{options['index']}/{len(snipes) - 1}")
    #
    #         await ctx.send(embed=e)
    #
    # @staticmethod
    # def get_proxy_fields(snipes: typing.Iterable) -> list:
    #     res = []
    #
    #     for snipe in snipes:
    #         # (6000 - (1,024 * 5)) / 5 = 176 max size my titles can be
    #         # 1,024 is the field value limit
    #         res.append(
    #             EmbedFieldProxy(
    #                 shorten(str(snipe), 176, placeholder="..."),
    #                 shorten(snipe.content, 1_024, placeholder="..."),
    #                 False,
    #             )
    #         )
    #
    #     return res
    #
    # def get_snipes(
    #     self,
    #     command_author: discord.Member,
    #     command_channel: discord.TextChannel,
    #     *,
    #     channel: discord.TextChannel = None,
    #     guild: bool = False,
    #     authors: typing.List[discord.Member] = None,
    #     before: int = None,
    #     after: int = None,
    #     mode: SnipeMode = None,
    #     contains: str = None,
    # ):
    #
    #     if channel is None and guild is None:
    #         raise ValueError("Channel and Guild cannot both be None.")
    #
    #     filters = [
    #         lambda snipe: snipe.channel.permissions_for(command_author).read_messages
    #     ]
    #
    #     if not command_channel.is_nsfw():
    #         filters.append(lambda snipe: not snipe.channel.is_nsfw())
    #
    #     if authors:
    #         author_ids = [a.id for a in authors]
    #         filters.append(lambda snipe: snipe.author.id in author_ids)
    #
    #     if before:
    #         filters.append(lambda snipe: snipe.id < before)
    #
    #     if after:
    #         filters.append(lambda snipe: snipe.id > after)
    #
    #     if mode:
    #         filters.append(lambda snipe: snipe.mode == mode)
    #
    #     if contains:
    #         to_match = " ".join(contains)
    #         filters.append(lambda snipe: to_match in snipe.content)
    #
    #     if guild:
    #         snipes = []
    #         snipe_channels = self.bot.snipes[channel.guild.id]
    #         for channel_snipes in snipe_channels.values():
    #             filtered = channel_snipes
    #             for _filter in filters:
    #                 filtered = list(filter(_filter, filtered))
    #             snipes.extend(filtered)
    #
    #         # need to be reordered by time, would be by channel otherwise
    #         snipes = list(reversed(sorted(snipes, key=lambda s: s.time)))
    #     else:
    #         snipes = self.bot.snipes[channel.guild.id][channel.id]
    #         for _filter in filters:
    #             snipes = list(filter(_filter, snipes))
    #
    #     return snipes


async def setup(bot):
    await bot.add_cog(Snipe(bot))
