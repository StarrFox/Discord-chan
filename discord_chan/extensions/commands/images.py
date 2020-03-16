# -*- coding: utf-8 -*-
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
from discord.ext import commands
from PIL.Image import Image

import discord_chan
from discord_chan import BetweenConverter, SubContext, ImageConverter, ImageDefault


# Todo: add more image commands
# Todo: add link converter than validates the url and accept attachments or prior images (channel history)
class Images(commands.Cog, name='images'):

    @commands.command()
    @commands.cooldown(1, 30, commands.cooldowns.BucketType.user)
    async def wallemoji(self,
                        ctx: SubContext,
                        name: str,
                        width: BetweenConverter(1, 10),
                        height: BetweenConverter(1, 10),
                        image: ImageConverter = ImageDefault):
        """
        Make some emojis from an image,
        Width and height must be between 1 and 10
        """
        image: Image

        gif = image.format == 'GIF'
        format = image.format

        with ctx.typing():
            factors = discord_chan.get_wallify_factors(image.size, (width, height))
            if gif:
                emojis = await discord_chan.wallify_gif_image(image, width, height)
            else:
                emojis = await discord_chan.wallify_image(image, width, height)

            premade_wall = discord_chan.get_wallify_example_file(factors.wall_size, name)

            archive = await discord_chan.tarball_images(emojis,
                                                        name=name,
                                                        animated=gif,
                                                        format=format,
                                                        extras=[(name + '.txt', premade_wall)])

        await ctx.send(
            ctx.author.mention,
            file=discord.File(archive, filename=f"{name}.tar"),
            escape_mentions=False,
            no_edit=True
        )

    # @commands.command(aliases=['randomize'])
    # @commands.cooldown(1, 30, commands.cooldowns.BucketType.user)
    # async def shuffle(self, ctx: commands.Context, link: str, degree: BetweenConverter(1, 100_000)):
    #     """
    #     Shuffle's an image's pixels
    #     Degree must be between 1 and 100,000
    #     """
    #     # Todo: use this for the image converter?
    #     try:
    #         image = await discord_chan.url_to_image(link)
    #     except discord_chan.FileTooLarge:
    #         return await ctx.send('File was too large.')
    #     except discord_chan.InvalidImageType:
    #         return await ctx.send('Unable to open file as image.')
    #
    #     with ctx.typing():
    #         shuffled = await discord_chan.shuffle_image(image, degree=degree)
    #
    #         file = await discord_chan.image_to_file(shuffled, f'shuffled.{shuffled.format.lower()}')
    #
    #     await ctx.send(ctx.author.mention, file=file)

    @commands.command(aliases=['diff'])
    @commands.cooldown(1, 30, commands.cooldowns.BucketType.user)
    async def difference(self,
                         ctx: SubContext,
                         image1: ImageConverter('png'),
                         image2: ImageConverter('png') = ImageDefault):
        """
        Get a composite image of two image's differences
        """
        # I could tell them which link caused but eh
        image1: Image
        image2: Image

        with ctx.typing():
            difference_image = await discord_chan.difference_image(image1, image2)

            file = await discord_chan.image_to_file(difference_image, f'difference.png')

        await ctx.send(ctx.author.mention, file=file, escape_mentions=False, no_edit=True)

    # @commands.command(aliases=['sim'])
    # @commands.cooldown(1, 30, commands.cooldowns.BucketType.user)
    # async def simularity(self, ctx: commands.Context):
    #     """
    #     Get the simularity rating of two images
    #     """
    #     pass


def setup(bot):
    bot.add_cog(Images())
