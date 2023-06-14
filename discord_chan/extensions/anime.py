import discord
from discord.ext import commands

import discord_chan
from discord_chan import DiscordChan, SubContext, checks


class Anime(commands.Cog, name="anime"):
    def __init__(self, bot: DiscordChan):
        self.bot = bot

    # TODO: figure out what needed to be fixed
    # TODO: fix
    @commands.command(aliases=["sb"])
    @checks.some_guilds([536702243119038464])
    @commands.is_nsfw()
    async def safebooru(self, ctx: SubContext, *tags: str):
        if post := await discord_chan.get_random_safebooru_post(list(tags)):
            embed = discord.Embed(
                description=f"Post {post.post_index+1}/{post.tag_post_count}"
            )
            embed.set_image(url=post.url)
            await ctx.send(embed=embed)
        else:
            await ctx.deny("No posts found")


async def setup(bot):
    await bot.add_cog(Anime(bot))
