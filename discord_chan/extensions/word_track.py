import asyncio
import re

import discord
from discord.ext import commands

import discord_chan
from discord_chan import DiscordChan
from discord_chan.menus import DCMenuPages, NormalPageSource

FEATURE_NAME = "word_track"
# number of seconds to wait for edits to messages before consuming
EDIT_GRACE_TIME = 15

WORD_SIZE_LIMIT = 15


class WordTrack(commands.Cog):
    def __init__(self, bot: DiscordChan):
        self.bot = bot

        self.pending_messages: dict[int, discord.Message] = {}

    async def consume_message(self, message_id: int):
        message = self.pending_messages.pop(message_id)

        words = self.split_words(message.content)

        # if their message was just "?" we'd get an empty list
        if not words:
            return

        assert message.guild is not None

        for word in set(words):
            # most words are under 15 characters
            if len(word) > WORD_SIZE_LIMIT:
                continue

            await self.bot.database.update_word_track_word(
                server_id=message.guild.id,
                author_id=message.author.id,
                word=word,
                amount=1,
            )

    @staticmethod
    def split_words(entry: str) -> list[str]:
        entry = re.sub(r"[^a-zA-Z _']", " ", entry.lower())
        return [e for e in entry.split(" ") if len(e) > 0]

    # TODO: make a better solution using bot.wait_for
    @commands.Cog.listener("on_message")
    async def message_event(self, message: discord.Message):
        if message.author.bot:
            return

        # dms
        if message.channel.guild is None:
            return

        if not await self.bot.is_feature_enabled(
            message.channel.guild.id, FEATURE_NAME
        ):
            return

        self.pending_messages[message.id] = message
        await asyncio.sleep(EDIT_GRACE_TIME)
        await self.consume_message(message.id)

    @commands.Cog.listener("on_message_edit")
    async def message_edit_event(self, old: discord.Message, new: discord.Message):
        if old.author.bot:
            return

        # dms
        if old.channel.guild is None:
            return

        if not await self.bot.is_feature_enabled(old.channel.guild.id, FEATURE_NAME):
            return

        if self.pending_messages.get(old.id):
            self.pending_messages[old.id] = new

    @commands.command(name="word_count")
    @commands.guild_only()
    async def word_count_command(
        self, ctx: commands.Context, target_member: discord.Member | None = None
    ):
        """
        Get word count leaderboard for the server or a member
        """
        # guild_only check should ensure this is true
        assert ctx.guild is not None

        leaderboard = await self.bot.database.get_server_word_track_leaderboard(
            server_id=ctx.guild.id,
            author_id=target_member.id if target_member is not None else None,
        )

        if not leaderboard:
            return await ctx.send("No results found")

        entries: list[str] = []

        for word, count in leaderboard.items():
            entries.append(f"- {word}: {count}")

        source = NormalPageSource(entries, per_page=10)
        menu = DCMenuPages(source)

        await menu.start(ctx)

    @commands.group(name=FEATURE_NAME, invoke_without_command=True, aliases=["wt"])
    @commands.guild_only()
    async def wt(self, ctx: commands.Context):
        # commands.guild_only prevents this
        assert ctx.guild is not None
        enabled = await self.bot.is_feature_enabled(ctx.guild.id, FEATURE_NAME)

        if enabled:
            return await ctx.send("Word track is enabled for this guild")
        else:
            return await ctx.send("Word track is not enabled for this guild")

    @wt.command()
    @discord_chan.checks.guild_owner()
    async def toggle(self, ctx: discord_chan.SubContext):
        """Toggle word track status"""
        assert ctx.guild is not None

        if await self.bot.is_feature_enabled(ctx.guild.id, FEATURE_NAME):
            await self.bot.set_feature_disabled(ctx.guild.id, FEATURE_NAME)
            return await ctx.confirm("Word track disabled")

        await self.bot.set_feature_enabled(ctx.guild.id, FEATURE_NAME)
        return await ctx.confirm("Word track enabled")


async def setup(bot: DiscordChan):
    await bot.add_cog(WordTrack(bot))
