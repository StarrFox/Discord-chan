import discord
from discord.ext import commands

import discord_chan
from discord_chan import DiscordChan, SubContext, checks
from discord_chan.menus import SafebooruEmbedStreamSource, DCMenuPages
from discord_chan import safebooru_api


SAFEBOORU_ALLOWED_GUILDS = [
    1233971885281378414,  # starrden
    536702243119038464,  # spoil
]


class Anime(commands.Cog, name="anime"):
    def __init__(self, bot: DiscordChan):
        self.bot = bot

    # TODO: add feature lock
    @commands.group(aliases=["sb"], invoke_without_command=True)
    # @checks.some_guilds(*SAFEBOORU_ALLOWED_GUILDS)
    async def safebooru(self, ctx: SubContext, *tags: str):
        if post := await discord_chan.get_random_safebooru_post(list(tags)):
            embed = discord.Embed(
                description=f"Post {post.post_index+1}/{post.tag_post_count}"
            )
            embed.set_image(url=post.url)
            await ctx.send(embed=embed)
        else:
            await ctx.deny("No posts found")

    @safebooru.command(name="list")
    async def safebooru_list(self, ctx: SubContext, *tags: str):
        post_count = await safebooru_api.get_safebooru_post_count(tags)
        if post_count > 0:
            source = SafebooruEmbedStreamSource(tags=tags, post_count=post_count)
            menu = DCMenuPages(source, show_random_button=True)
            await menu.start()
        else:
            await ctx.deny("No posts found")


async def setup(bot):
    await bot.add_cog(Anime(bot))
