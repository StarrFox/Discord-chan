from typing import Annotated

import discord
from discord.ext import commands
from PIL.Image import Image as PilImage

import discord_chan
from discord_chan import BetweenConverter, ImageConverter, LastImage, SubContext


class Images(commands.Cog, name="images"):
    @commands.command()
    @commands.cooldown(1, 30, commands.cooldowns.BucketType.user)
    async def wallemoji(
        self,
        ctx: SubContext,
        name: str,
        width: Annotated[int, BetweenConverter(1, 10)],
        height: Annotated[int, BetweenConverter(1, 10)],
        image: Annotated[PilImage, ImageConverter] = LastImage,
    ):
        """
        Make some emojis from an image,
        Width and height must be between 1 and 10
        """
        gif = image.format == "GIF"
        format = image.format

        async with ctx.typing():
            factors = discord_chan.image.get_wallify_factors(image.size, (width, height))
            if gif:
                emojis = await discord_chan.image.wallify_gif_image(image, width, height)
            else:
                emojis = await discord_chan.image.wallify_image(image, width, height)

            premade_wall = discord_chan.image.get_wallify_example_file(
                factors.wall_size, name
            )

            archive = await discord_chan.image.tarball_images(
                emojis,
                name=name,
                animated=gif,
                format=format,
                extras=[(name + ".txt", premade_wall)],
            )

        await ctx.send(
            ctx.author.mention, file=discord.File(archive, filename=f"{name}.tar")
        )

    @commands.command(aliases=["diff"])
    @commands.cooldown(1, 30, commands.cooldowns.BucketType.user)
    async def difference(
        self,
        ctx: SubContext,
        image1: Annotated[PilImage, ImageConverter("png")],
        image2: Annotated[PilImage, ImageConverter("png")] = LastImage,
    ):
        """
        Get a composite image of two image's differences
        """
        async with ctx.typing():
            difference_image = await discord_chan.image.difference_image(image1, image2)

            file = await discord_chan.image.image_to_file(
                difference_image, "difference.png"
            )

        await ctx.send(ctx.author.mention, file=file)


async def setup(bot: commands.Bot):
    await bot.add_cog(Images())
