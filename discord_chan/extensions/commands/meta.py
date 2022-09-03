import discord
from discord.ext import commands

from discord_chan import BotConverter


class Meta(commands.Cog, name="meta"):
    """Informational commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """
        Sends the bot's websocket latency
        """
        await ctx.send(
            f"\N{TABLE TENNIS PADDLE AND BALL} {round(ctx.bot.latency * 1000)}ms"
        )

    @commands.command()
    async def invite(
        self,
        ctx: commands.Context,
        bot: BotConverter = None,
    ):
        """
        Get the invite link for a bot,
        defaults to myself
        """
        if bot is None:
            bot = ctx.me

        bot: discord.Member

        url = discord.utils.oauth_url(bot.id)
        await ctx.send(url)

    @commands.command()
    async def source(self, ctx: commands.Context):
        """
        Links to the bot's source url
        """
        await ctx.send("https://github.com/StarrFox/Discord-chan")


async def setup(bot):
    cog = Meta(bot)
    await bot.add_cog(cog)
    bot.help_command.cog = cog


async def teardown(bot):
    bot.help_command.cog = None
