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

from functools import partial
from io import BytesIO
from tarfile import TarFile, TarInfo

import discord
from PIL import Image, ImageSequence
from discord.ext import commands


def get_premade_wall(name: str, collum_num: int, row_num: int):
    """
    Returns a premade wall
    EX:
    ```
    :kitty_0::kitty_1:
    :kitty_2::kitty_3:
    ```
    """
    text = '```\n'
    for row in range(row_num):
        for collum in range(collum_num):
            place = (collum_num * row) + collum
            text += f':{name}_{place}:'
        text += '\n'
    text += '\n```'

    file_bytes = bytes(text, 'utf-8')

    file = BytesIO(file_bytes)

    file_info = TarInfo("Premade_wall.txt")
    file_info.size = len(file.getbuffer())

    file.seek(0)

    return file_info, file


def zip_emojis(emojis: list, name: str, premade_wall: tuple):
    fp = BytesIO()
    zip = TarFile(mode='w', fileobj=fp)

    for idx, emoji in enumerate(emojis):
        f = BytesIO()
        emoji.save(f, "png")
        f.seek(0)
        info = TarInfo(f"{name}_{idx}.png")
        info.size = len(f.getbuffer())
        zip.addfile(info, fileobj=f)

    zip.addfile(premade_wall[0], fileobj=premade_wall[1])

    fp.seek(0)
    return fp


def zip_gif_emojis(emojis: list, name: str, premade_wall: tuple):
    """
    same as normal but emojis is a list of frame lists
    """
    fp = BytesIO()
    zip = TarFile(mode='w', fileobj=fp)

    for idx, emoji in enumerate(emojis):
        f = BytesIO()
        emoji[0].save(f, "gif", append_images=emoji[1:], save_all=True, loop=0)
        f.seek(0)
        info = TarInfo(f"{name}_{idx}.gif")
        info.size = len(f.getbuffer())
        zip.addfile(info, fileobj=f)

    zip.addfile(premade_wall[0], fileobj=premade_wall[1])

    fp.seek(0)
    return fp


class wallemojis(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def make_emojis(self, img: Image, name: str, wall_width: int, wall_height: int, gif: bool):
        img_width, img_height = img.size

        emoji_width = img_width // wall_width
        emoji_height = img_height // wall_height

        new_width = (img_width // emoji_width) * emoji_width
        new_height = (img_height // emoji_height) * emoji_height

        num_of_collums = new_width // emoji_width
        num_of_rows = new_height // emoji_height

        premade_wall = get_premade_wall(
            name,
            num_of_collums,
            num_of_rows
        )

        emojis = []

        if gif:
            for row in range(num_of_rows):
                for collum in range(num_of_collums):
                    frames = []

                    for page in ImageSequence.Iterator(img):
                        page = page.resize((new_width, new_height))
                        frames.append(page.crop((
                            collum * emoji_width,
                            row * emoji_height,
                            (collum * emoji_width) + emoji_width,
                            (row * emoji_height) + emoji_height
                        )))

                    emojis.append(frames)

            return zip_gif_emojis(emojis, name, premade_wall)

        else:

            img = img.resize((new_width, new_height))

            for row in range(num_of_rows):
                for collum in range(num_of_collums):
                    emojis.append(img.crop((
                        collum * emoji_width,
                        row * emoji_height,
                        (collum * emoji_width) + emoji_width,
                        (row * emoji_height) + emoji_height
                    )))

            return zip_emojis(emojis, name, premade_wall)

    async def get_bytes(self, link):
        async with self.bot.session.get(link) as res:
            return await res.read(), res.content_type

    @commands.command()
    @commands.cooldown(1, 30, commands.cooldowns.BucketType.user)
    async def wallemoji(self, ctx: commands.Context, name: str, width: int, height: int, link: str):
        """
        Makes some emojis from an image
        """
        if not 0 < height <= 10 or not 0 < width <= 10:
            return await ctx.send("Only use sizes between 0 and 10")

        width, height = (round(width), round(height))
        _bytes, file_type = await self.get_bytes(link)

        if "image" not in file_type.lower():
            return await ctx.send("Link was not to an image")

        gif = "gif" in file_type.lower()
        img = Image.open(BytesIO(_bytes))

        func = partial(
            self.make_emojis,
            img,
            name,
            width,
            height,
            gif
        )

        with ctx.typing():
            archive = await self.bot.loop.run_in_executor(None, func)

        await ctx.send(file=discord.File(archive, filename=f"{name}.tar"))


def setup(bot):
    bot.add_cog(wallemojis(bot))
