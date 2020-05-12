#  Copyright © 2019 StarrFox
#
#  Discord Chan is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Discord Chan is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with Discord Chan.  If not, see <https://www.gnu.org/licenses/>.

import discord
from PIL.Image import Image
from discord.ext import commands

import discord_chan
from discord_chan import BetweenConverter, ImageConverter, ImageDefault, SubContext


# Todo: add more image commands
class Images(commands.Cog, name="images"):
    @commands.command()
    @commands.cooldown(1, 30, commands.cooldowns.BucketType.user)
    async def wallemoji(
        self,
        ctx: SubContext,
        name: str,
        width: BetweenConverter(1, 10),
        height: BetweenConverter(1, 10),
        image: ImageConverter = ImageDefault,
    ):
        """
        Make some emojis from an image,
        Width and height must be between 1 and 10
        """
        image: Image

        gif = image.format == "GIF"
        format = image.format

        with ctx.typing():
            factors = discord_chan.get_wallify_factors(image.size, (width, height))
            if gif:
                emojis = await discord_chan.wallify_gif_image(image, width, height)
            else:
                emojis = await discord_chan.wallify_image(image, width, height)

            premade_wall = discord_chan.get_wallify_example_file(
                factors.wall_size, name
            )

            archive = await discord_chan.tarball_images(
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
        image1: ImageConverter("png"),
        image2: ImageConverter("png") = ImageDefault,
    ):
        """
        Get a composite image of two image's differences
        """
        image1: Image
        image2: Image

        with ctx.typing():
            difference_image = await discord_chan.difference_image(image1, image2)

            file = await discord_chan.image_to_file(difference_image, "difference.png")

        await ctx.send(ctx.author.mention, file=file)

    # @commands.command(aliases=['sim'])
    # @commands.cooldown(1, 30, commands.cooldowns.BucketType.user)
    # async def simularity(self, ctx: commands.Context):
    #     """
    #     Get the simularity rating of two images
    #     """
    #     pass


def setup(bot):
    bot.add_cog(Images())
