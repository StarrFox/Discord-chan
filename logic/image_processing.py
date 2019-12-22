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
from tarfile import TarFile, TarInfo

from PIL import Image, ImageSequence

import aiohttp
from jishaku.functools import executor_function


async def get_bytes(link: str):
    async with aiohttp.ClientSession().get(link) as res:
        return await res.read(), res.content_type


class WallEmojis:

    def __init__(self, image: Image, name: str, wall_width: int, wall_height: int, gif: bool):
        self.image = image
        self.name = name
        self.wall_width = wall_width
        self.wall_height = wall_height
        self.gif = gif

        self.img_width, self.img_height = self.image.size

        self.emoji_width = self.img_width // self.wall_width
        self.emoji_height = self.img_height // self.wall_height

        self.new_width = (self.img_width // self.emoji_width) * self.emoji_width
        self.new_height = (self.img_height // self.emoji_height) * self.emoji_height

        self.num_of_collums = self.new_width // self.emoji_width
        self.num_of_rows = self.new_height // self.emoji_height

    @property
    def premade_wall(self):
        """
        Returns a premade wall
        EX:
        ```
        :kitty_0::kitty_1:
        :kitty_2::kitty_3:
        ```
        """
        text = '```\n'
        for row in range(self.num_of_rows):
            for collum in range(self.num_of_collums):
                place = (self.num_of_collums * row) + collum
                text += f':{self.name}_{place}:'
            text += '\n'
        text += '\n```'

        file_bytes = bytes(text, 'utf-8')

        file = BytesIO(file_bytes)

        file_info = TarInfo("Premade_wall.txt")
        file_info.size = len(file.getbuffer())

        file.seek(0)

        return file_info, file

    @executor_function
    def make_emojis(self):
        emojis = []

        img = self.image.resize((self.new_width, self.new_height))

        for row in range(self.num_of_rows):
            for collum in range(self.num_of_collums):
                emojis.append(img.crop((
                    collum * self.emoji_width,
                    row * self.emoji_height,
                    (collum * self.emoji_width) + self.emoji_width,
                    (row * self.emoji_height) + self.emoji_height
                )))

        return self.zip_emojis(emojis)

    @executor_function
    def make_gif_emojis(self):
        emojis = []
        for row in range(self.num_of_rows):
            for collum in range(self.num_of_collums):
                frames = []

                for page in ImageSequence.Iterator(self.image):
                    page = page.resize((self.new_width, self.new_height))
                    frames.append(page.crop((
                        collum * self.emoji_width,
                        row * self.emoji_height,
                        (collum * self.emoji_width) + self.emoji_width,
                        (row * self.emoji_height) + self.emoji_height
                    )))

                emojis.append(frames)

        return self.zip_gif_emojis(emojis)

    def zip_emojis(self, emojis: list):
        fp = BytesIO()
        tar = TarFile(mode='w', fileobj=fp)

        for idx, emoji in enumerate(emojis):
            f = BytesIO()
            emoji.save(f, "png")
            f.seek(0)
            info = TarInfo(f"{self.name}_{idx}.png")
            info.size = len(f.getbuffer())
            tar.addfile(info, fileobj=f)

        premade_wall = self.premade_wall
        tar.addfile(premade_wall[0], fileobj=premade_wall[1])

        fp.seek(0)
        return fp

    def zip_gif_emojis(self, emojis: list):
        """
        same as normal but emojis is a list of frame lists
        """
        fp = BytesIO()
        tar = TarFile(mode='w', fileobj=fp)

        for idx, emoji in enumerate(emojis):
            f = BytesIO()
            emoji[0].save(f, "gif", append_images=emoji[1:], save_all=True, loop=0)
            f.seek(0)
            info = TarInfo(f"{self.name}_{idx}.gif")
            info.size = len(f.getbuffer())
            tar.addfile(info, fileobj=f)

        premade_wall = self.premade_wall
        tar.addfile(premade_wall[0], fileobj=premade_wall[1])

        fp.seek(0)
        return fp

    async def run(self):
        if self.gif:
            return await self.make_emojis()
        else:
            return await self.make_gif_emojis()
