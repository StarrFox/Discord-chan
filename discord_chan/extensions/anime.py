import discord
from discord.ext import commands

import discord_chan
from discord_chan import DiscordChan, checks, SubContext


THICK_TABLE = str.maketrans(
    {
        "a": "卂",
        "b": "乃",
        "c": "匚",
        "d": "刀",
        "e": "乇",
        "f": "下",
        "g": "厶",
        "h": "卄",
        "i": "工",
        "j": "丁",
        "k": "长",
        "l": "乚",
        "m": "从",
        "n": "𠘨",
        "o": "口",
        "p": "尸",
        "q": "㔿",
        "r": "尺",
        "s": "丂",
        "t": "丅",
        "u": "凵",
        "v": "リ",
        "w": "山",
        "x": "乂",
        "y": "丫",
        "z": "乙",
        " ": "   ",
    }
)


class Anime(commands.Cog, name="anime"):
    def __init__(self, bot: DiscordChan):
        self.bot = bot

    @commands.command()
    async def thickify(self, ctx: SubContext, *, message: str):
        """
        thickify text
        """
        await ctx.send(message.lower().translate(THICK_TABLE))

    # TODO: fix
    @commands.command(aliases=["sb"])
    @checks.some_guilds([536702243119038464])
    @commands.is_nsfw()
    async def safebooru(self, ctx: SubContext, *tags: str):
        if post := await discord_chan.get_random_safebooru_post(list(tags)):
            embed = discord.Embed(description=f"Post {post.post_index+1}/{post.tag_post_count}")
            embed.set_image(url=post.url)
            await ctx.send(embed=embed)
        else:
            await ctx.deny("No posts found")


async def setup(bot):
    await bot.add_cog(Anime(bot))
