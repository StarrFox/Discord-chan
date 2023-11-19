import asyncio
import contextlib
import re

import discord
from discord.ext import commands

import discord_chan
from discord_chan import DiscordChan
from discord_chan.menus import DCMenuPages, NormalPageSource

# number of seconds to wait for edits to messages before consuming
EDIT_GRACE_TIME = 15

WORD_SIZE_LIMIT = 20


class WordTrack(commands.Cog):
    def __init__(self, bot: DiscordChan):
        self.bot = bot

    async def consume_message(self, message: discord.Message):
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

    @commands.Cog.listener("on_message")
    async def message_event(self, message: discord.Message):
        if message.author.bot:
            return

        # dms
        if message.guild is None:
            return

        if not await self.bot.feature_manager.is_enabled(discord_chan.Feature.word_track, message.guild.id):
            return

        async def _wait_for_edits():
            edited_message = message

            with contextlib.suppress(asyncio.CancelledError):
                while True:
                    edited_message = await self.bot.wait_for(
                        "message", check=lambda m: m.id == message.id
                    )

            return edited_message

        message = await asyncio.wait_for(_wait_for_edits(), timeout=EDIT_GRACE_TIME)
        await self.consume_message(message)

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

        total = len(entries)

        entries = [f"total = {total}", ""] + entries

        source = NormalPageSource(entries, per_page=10)
        menu = DCMenuPages(source)

        await menu.start(ctx)


async def setup(bot: DiscordChan):
    await bot.add_cog(WordTrack(bot))
