from io import BytesIO
from typing import Annotated, Literal

import discord
from discord.ext import commands
from PIL.Image import Image as PilImage

import discord_chan
from discord_chan import BetweenConverter, ImageConverter, LastImage, SubContext
from discord_chan.menus import DCMenuPages, NormalPageSource


class Images(commands.Cog, name="images"):
    @commands.command()
    @commands.cooldown(1, 30, commands.cooldowns.BucketType.user)
    async def wallemoji(
        self,
        ctx: SubContext,
        name: str = commands.parameter(description="name prefix of the emojis"),
        width: Annotated[int, BetweenConverter(1, 10)] = commands.parameter(
            description="width (in emojis); must be between 1 and 10"
        ),
        height: Annotated[int, BetweenConverter(1, 10)] = commands.parameter(
            description="height (in emojis); must be between 1 and 10"
        ),
        image: Annotated[PilImage, ImageConverter] = LastImage,
    ):
        """
        Make some emojis from an image
        """
        if image.format is None:
            return await ctx.send("Image format could not be read")

        gif = image.format == "GIF"
        format = image.format

        async with ctx.typing():
            factors = discord_chan.image.get_wallify_factors(
                image.size, (width, height)
            )
            if gif:
                emojis = await discord_chan.image.wallify_gif_image(
                    image, width, height
                )
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
    @commands.cooldown(1, 1, commands.cooldowns.BucketType.user)
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

    @commands.command(aliases=["gray"])
    @commands.cooldown(1, 1, commands.cooldowns.BucketType.user)
    async def grayscale(
        self,
        ctx: SubContext,
        image: Annotated[PilImage, ImageConverter("png")] = LastImage,
    ):
        """
        Make an image grayscale
        """
        async with ctx.typing():
            grayscale_image = await discord_chan.image.grayscale_image(image)

            file = await discord_chan.image.image_to_file(
                grayscale_image, "grayscale.png"
            )

        await ctx.send(ctx.author.mention, file=file)

    # TODO: add gif support
    @commands.group(aliases=["mono"], invoke_without_command=True)
    @commands.cooldown(1, 1, commands.cooldowns.BucketType.user)
    async def monochromatic(
        self,
        ctx: SubContext,
        image: Annotated[PilImage, ImageConverter("png")] = LastImage,
        method: Literal["kapur", "otsu", "triangle"] = "kapur",
    ):
        """
        Make an image monochromatic
        """
        async with ctx.typing():
            # TODO: make allow ImageConverter to return wand images
            buffer = BytesIO()
            image.save(buffer, "png")
            buffer.seek(0)

            monochromatic_image = await discord_chan.image.monochomize_image(
                buffer.read(),
                method,
            )

            file = discord.File(monochromatic_image, "monochromatic.png")

        await ctx.send(ctx.author.mention, file=file)

    @monochromatic.command(name="all")
    @commands.cooldown(1, 10, commands.cooldowns.BucketType.user)
    async def monochromatic_all(
        self,
        ctx: SubContext,
        image: Annotated[PilImage, ImageConverter("png")] = LastImage,
    ):
        """
        Make an image monochromatic in all methods
        """
        async with ctx.typing():
            files: list[discord.File] = []

            for method in ("kapur", "otsu", "triangle"):
                # TODO: make allow ImageConverter to return wand images
                buffer = BytesIO()
                image.save(buffer, "png")
                buffer.seek(0)

                monochromatic_image = await discord_chan.image.monochomize_image(
                    buffer.read(),
                    method,
                )

                files.append(discord.File(monochromatic_image, f"{method}.png"))

        await ctx.send(ctx.author.mention, files=files)

    @commands.group(invoke_without_command=True)
    async def colors(
        self,
        ctx: SubContext,
        image: Annotated[PilImage, ImageConverter("png")] = LastImage,
    ):
        """
        View the colors of an image
        """
        colors = await discord_chan.image.get_image_colors(image)

        if colors is None:
            return await ctx.send("Could not discern colors of image")

        entries: list[str] = []

        for percent, color in colors.items():
            entries.append(f"{round(percent * 100, 3)}%: RGBA{color}")

        source = NormalPageSource(entries, per_page=10)
        menu = DCMenuPages(source)

        await menu.start(ctx)


async def setup(bot: commands.Bot):
    await bot.add_cog(Images())
