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

from io import BytesIO

import discord
from PIL import Image
from discord.ext import commands

from logic.image_processing import get_bytes, WallEmojis


class wallemojis(commands.Cog):

    # TODO: test this
    @commands.command()
    @commands.cooldown(1, 30, commands.cooldowns.BucketType.user)
    async def wallemoji(self, ctx: commands.Context, name: str, width: int, height: int, link: str):
        """
        Makes some emojis from an image
        """
        # Todo: change this to be a converter
        if not 1 < height <= 10 or not 1 < width <= 10:
            return await ctx.send("Only use sizes between 1 and 10")

        width, height = (round(width), round(height))
        _bytes, file_type = await get_bytes(link)

        if "image" not in file_type.lower():
            return await ctx.send("Link was not to an image")

        gif = "gif" in file_type.lower()
        img = Image.open(BytesIO(_bytes))

        generator = WallEmojis(img, name, width, height, gif)

        with ctx.typing():
            archive = await generator.run()

        await ctx.send(file=discord.File(archive, filename=f"{name}.tar"))

def setup(bot):
    bot.add_cog(wallemojis())
