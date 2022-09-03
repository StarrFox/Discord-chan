import json
import unicodedata

import discord
import humanize
import uwuify
from discord.ext import commands


from discord_chan import (
    BetweenConverter,
    DCMenuPages,
    DiscordChan,
    FetchedMember,
    FetchedUser,
    NormalPageSource,
    PartitionPaginator,
    PrologPaginator,
    SubContext,
    TimeConverter,
)

try:
    from enchant.checker import SpellChecker
except ImportError:
    SpellChecker = None


class General(commands.Cog, name="general"):
    """General use commands"""

    def __init__(self, bot: DiscordChan):
        self.bot = bot

    @commands.command()
    async def charinfo(self, ctx: commands.Context, *, characters):
        """
        Convert characters to name syntax, or unicode if name isn't found.
        """
        paginator = PartitionPaginator(
            prefix=None, suffix=None, max_size=300, wrap_on=("}", "\n")
        )

        final = ""
        for char in characters:
            try:
                name = unicodedata.name(char)
                final += f"\\N{{{name}}}\n"
            except ValueError:
                final += f"\\U{ord(char):0>8x}\n"

        paginator.add_line(final)

        source = NormalPageSource(paginator.pages)

        menu = DCMenuPages(source)

        await menu.start(ctx)

    @commands.command()
    async def time_convert(self, ctx: commands.Context, *times: TimeConverter):
        await ctx.send(f"total={sum(times)}\n\n{times}")

    @commands.command()
    async def say(self, ctx: commands.Context, *, message: str):
        """
        Have the bot say something
        """
        await ctx.send(message)

    @commands.command(aliases=["owoify", "owo", "uwu"])
    async def uwuify(self, ctx: commands.Context, *, message: str):
        """UwUifies text"""
        await ctx.send(uwuify.uwu(message, flags=uwuify.SMILEY))

    @commands.command(aliases=["spell"])
    async def spellcheck(self, ctx: commands.Context, *, text: str):
        """
        Spellcheck text
        """
        if SpellChecker is None:
            return await ctx.send("Spell checking is not enabled.")

        checker = SpellChecker("en_US", text)

        for error in checker:
            error.replace(str(error.suggest()))

        await ctx.send(checker.get_text())

    @commands.command()
    async def clean(self, ctx: SubContext, amount: BetweenConverter(1, 100) = 10):
        """
        Delete's the bot's last <amount> message(s)
        amount must be between 1 and 100, defaulting to 10
        """

        def check(message):
            return message.author == ctx.me

        can_mass_delete = ctx.channel.permissions_for(ctx.me).manage_messages

        await ctx.channel.purge(limit=amount, check=check, bulk=can_mass_delete)
        await ctx.confirm("Messages cleaned.")

    @commands.command(aliases=["avy", "pfp"])
    async def avatar(self, ctx: commands.Context, member: FetchedUser = None):
        """
        Get a member's avatar
        """
        if member is None:
            member = await ctx.guild.fetch_member(ctx.author.id)

        member: discord.Member
        await ctx.send(str(member.avatar_url))

    @commands.command(aliases=["mi", "userinfo", "ui"])
    async def memberinfo(
        self, ctx: commands.Context, member: FetchedMember = None
    ):
        """
        Get info on a guild member
        """
        if member is None:
            member = await ctx.guild.fetch_member(ctx.author.id)

        data = {
            "id": member.id,
            "top role": member.top_role.name,
            "joined guild": humanize.naturaldate(member.joined_at),
            "joined discord": humanize.naturaldate(member.created_at),
        }

        paginator = PrologPaginator()

        paginator.recursively_add_dictonary({member.name: data})

        source = NormalPageSource(paginator.pages)

        menu = DCMenuPages(source)

        await menu.start(ctx)

    @commands.command(aliases=["si", "gi", "serverinfo"])
    async def guildinfo(self, ctx: commands.Context):
        """
        Get info on a guild
        """
        guild = await self.bot.fetch_guild(ctx.guild.id)

        # I don't have guild.channels
        channels = await guild.fetch_channels()

        data = {
            "id": guild.id,
            "owner": str(await self.bot.fetch_user(guild.owner_id)),
            "created": humanize.naturaltime(guild.created_at),
            "# of roles": len(guild.roles),
            "members": guild.approximate_member_count,
            "channels": {
                "categories": len(
                    [c for c in channels if isinstance(c, discord.CategoryChannel)]
                ),
                "text": len(
                    [c for c in channels if isinstance(c, discord.TextChannel)]
                ),
                "voice": len(
                    [c for c in channels if isinstance(c, discord.VoiceChannel)]
                ),
                "total": len(channels),
            },
        }

        paginator = PrologPaginator()
        paginator.recursively_add_dictonary({guild.name: data})
        source = NormalPageSource(paginator.pages)
        menu = DCMenuPages(source)

        await menu.start(ctx)

    @commands.group(invoke_without_command=True)
    async def raw(self, ctx: commands.Context):
        """
        Base raw command
        just sends help for raw
        """
        await ctx.send_help("raw")

    @staticmethod
    async def send_raw(ctx: commands.Context, data: dict):

        paginator = PartitionPaginator(prefix="```json", max_size=1985)
        to_send = json.dumps(data, indent=4)
        paginator.add_line(to_send)
        source = NormalPageSource(paginator.pages)
        menu = DCMenuPages(source)

        await menu.start(ctx)

    @raw.command(aliases=["msg"])
    async def message(
        self,
        ctx: commands.Context,
        message: discord.Message = None,
    ):
        """
        Raw message object,
        can provide channel with channel_id-message-id
        (shift-click copy id)
        """
        if message is None:
            message = ctx.message

        data = await self.bot.http.get_message(message.channel.id, message.id)
        await self.send_raw(ctx, data)

    @raw.command()
    async def channel(
        self, ctx: commands.Context, channel: discord.TextChannel = None
    ):
        """
        Raw channel object
        """
        if channel is None:
            channel = ctx.channel
        data = await self.bot.http.get_channel(channel.id)
        await self.send_raw(ctx, data)

    @raw.command()
    async def member(
        self, ctx: commands.Context, member: FetchedMember = None
    ):
        """
        Raw member object
        """
        if member is None:
            member = await ctx.guild.fetch_member(ctx.author.id)

        data = await self.bot.http.get_member(member.guild.id, member.id)
        await self.send_raw(ctx, data)

    @raw.command()
    async def user(
        self,
        ctx: commands.Context,
        userid: int = None,
    ):
        """
        Raw user object
        """
        if userid is None:
            userid = ctx.author.id

        try:
            data = await self.bot.http.get_user(userid)
        except discord.errors.NotFound:
            await ctx.send("Invalid user id")
        else:
            await self.send_raw(ctx, data)

    @raw.command(aliases=["server"])
    async def guild(self, ctx: commands.Context):
        """
        Raw guild object
        """
        data = await self.bot.http.get_guild(ctx.guild.id)
        await self.send_raw(ctx, data)

    # I don't use the invite converter to save api calls
    @raw.command()
    async def invite(self, ctx: commands.Context, invite: str):
        """
        Raw invite object
        """
        try:
            data = await self.bot.http.get_invite(invite.split("/")[-1])
        except discord.errors.NotFound:
            await ctx.send("Invalid invite.")
        else:
            await self.send_raw(ctx, data)

    @raw.command()
    async def emoji(self, ctx: commands.Context, emoji: discord.Emoji):
        """
        Raw emoji object
        """
        data = await self.bot.http.get_custom_emoji(emoji.guild.id, emoji.id)
        await self.send_raw(ctx, data)

    @raw.command()
    async def role(self, ctx: commands.Context, role: discord.Role):
        """
        Raw role object
        """
        data = await self.bot.http.get_roles(role.guild.id)
        role_data = discord.utils.find(lambda d: d["id"] == str(role.id), data)
        await self.send_raw(ctx, role_data)


async def setup(bot):
    await bot.add_cog(General(bot))
