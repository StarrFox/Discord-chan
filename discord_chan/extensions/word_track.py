import asyncio
import contextlib
import re

import discord
from discord.ext import commands

import discord_chan
from discord_chan import DiscordChan
from discord_chan.context import SubContext
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

        if not await self.bot.feature_manager.is_enabled(
            discord_chan.Feature.word_track, message.guild.id
        ):
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

    @commands.group(name="words", invoke_without_command=True, aliases=["word"])
    @commands.guild_only()
    async def words_command(self, ctx: SubContext):
        """
        Get word count leaderboard for the server
        """
        leaderboard = await self.bot.database.get_server_word_track_leaderboard(server_id=ctx.guild.id)

        if not leaderboard:
            return await ctx.send("No results found")

        entries: list[str] = []

        for word, count in leaderboard.items():
            entries.append(f"- {word}: {count}")

        source = NormalPageSource(entries, per_page=10)
        menu = DCMenuPages(source)

        await menu.start(ctx)

    @words_command.command(name="user", aliases=["member"])
    async def words_user(self, ctx: SubContext, member: discord.Member = commands.Author, *words: str):
        """
        Get word count leaderboard for a member
        """
        leaderboard = await self.bot.database.get_server_word_track_leaderboard(
            server_id=ctx.guild.id,
            author_id=member.id,
        )

        if not leaderboard:
            return await ctx.send("No results found")

        entries: list[str] = []

        for word, count in leaderboard.items():
            if words and word not in words:
                continue

            entries.append(f"- {word}: {count}")

        source = NormalPageSource(entries, per_page=10)
        menu = DCMenuPages(source)

        await menu.start(ctx)

    @words_command.command(name="stat", aliases=["stats"])
    async def words_stats(
        self,
        ctx: SubContext,
        member: discord.Member = commands.Author
    ):
        """
        Get word count stats for a member
        """
        leaderboard = await self.bot.database.get_server_word_track_leaderboard(
            server_id=ctx.guild.id,
            author_id=member.id,
        )

        if not leaderboard:
            return await ctx.send("No results found")

        unique_words = len(leaderboard.keys())
        total_words = sum(leaderboard.values())

        word_density = unique_words / total_words

        await ctx.reply(
            f"unique words: {unique_words}\ntotal words: {total_words}\n"
            f"word density: {round(word_density, 2)}",
            mention_author=False
        )

    @words_command.command(name="rank")
    async def words_rank(self, ctx: SubContext, word: str):
        """
        Get rank info on a word
        """
        # we only store lowercase versions of words
        word = word.lower()

        server_leaderboard = await self.bot.database.get_server_word_track_leaderboard(server_id=ctx.guild.id)

        if not server_leaderboard:
            return await ctx.send("word has not been used in server")
    
        try:
            server_count = server_leaderboard[word]
        except KeyError:
            return await ctx.send("word has not been used in server")

        server_rank = list(server_leaderboard.keys()).index(word) + 1

        member_loaderboard = await self.bot.database.get_member_bound_word_rank(server_id=ctx.guild.id, word=word)

        # this shouldn't be possible
        if not member_loaderboard:
            raise RuntimeError("somehow word was not found for member lookup")

        message_parts = [f"server count: {server_count}", f"server rank: {server_rank}", ""]

        for user_id, count in member_loaderboard[:5]:
            member = ctx.guild.get_member(user_id)

            if member is None:
                try:
                    user = await ctx.bot.fetch_user(user_id)
                except discord.NotFound:
                    # deleted account
                    user_name = str(user_id)
                else:
                    user_name = user.display_name
            else:
                user_name = member.mention

            message_parts.append(f"{user_name}: {count}")

        await ctx.send("\n".join(message_parts))


async def setup(bot: DiscordChan):
    await bot.add_cog(WordTrack(bot))
