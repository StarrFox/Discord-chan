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

from collections import namedtuple
from io import BytesIO
from random import randint
from tarfile import TarFile, TarInfo
from typing import Tuple, List, Optional

import aiohttp
from PIL import Image, ImageSequence, ImageChops
from discord import File
from imagehash import phash, ImageHash
from jishaku.functools import executor_function


# Todo: better manage the executors? use an internal loop and queue to fire them?

class ImageError(Exception):
    pass


class FileTooLarge(ImageError):
    pass


class InvalidImageType(ImageError):
    pass


TypedBytes = namedtuple('TypedBytes', 'file_bytes content_type')

# Getting images

async def get_bytes(link: str, *, max_length: int = 100) -> TypedBytes:
    """
    Get bytes and content_type from a link
    :param link: URL to the file
    :param max_length: Max file size to download in MB
    :return: TypedBytes representing the bytes and content_type
    :raise FileTooLarge: If the file was beyond max_length
    """
    # Bytes *1000 -> kb *1000 -> MB
    max_length = round((max_length / 1000) / 1000)
    async with aiohttp.ClientSession().get(link) as response:

        # Todo: handle these
        response.raise_for_status()

        if response.content_length > max_length:
            raise FileTooLarge(f'{response.content_length} is over max size of {max_length}.')

        return TypedBytes(
            file_bytes=await response.read(),
            content_type=response.content_type
        )


async def url_to_image(link: str) -> Image.Image:
    """
    Convence function to convert a link to a PIL Image
    :param link: The url of the image
    :return: Image representing the image
    :raises InvalidImage, FileTooLarge: PIL could not open the file
    """
    image_bytes, content_type = await get_bytes(link, max_length=20)

    # Todo: get the exact formats the running PIL supports
    # Check before to try and save some memory
    if 'image' not in content_type.lower():
        raise InvalidImageType(content_type)

    file_obj = BytesIO(image_bytes)

    @executor_function
    def open_image(img):
        return Image.open(img)

    try:
        image = await open_image(file_obj)
    except IOError:
        # This should never get here
        raise InvalidImageType(content_type)

    return image

# Saving images

@executor_function
def tarball_images(
        images: List[Image.Image],
        *,
        name: str = None,
        animated: bool = False,
        format: str = 'png',
        extras: List[Tuple[str, BytesIO]]) -> BytesIO:
    fp = BytesIO()
    tar = TarFile(mode='w', fileobj=fp)

    for idx, image in enumerate(images):
        f = BytesIO()
        if animated:
            image[0].save(f, format, append_images=image[1:], save_all=True, loop=0)
        else:
            image.save(f, format)

        f.seek(0)
        if name:
            info = TarInfo(f"{name}_{idx}.{format}")
        else:
            info = TarInfo(f"{idx}.{format}")
        info.size = len(f.getbuffer())
        tar.addfile(info, fileobj=f)

    for extra in extras:
        info = TarInfo(extra[0] or '_.txt')
        info.size = len(extra[1].getbuffer())
        tar.addfile(info, fileobj=extra[1])

    fp.seek(0)
    return fp


@executor_function
def image_to_file(image: Image.Image, filename: str = None) -> File:
    """
    Saves an image into a :class:discord.File
    :param image: The image to save
    :param filename: The filename to use
    :return: The File ready to send
    """
    buffer = BytesIO()

    image.save(buffer)

    return File(buffer, filename=filename)

# Image helpers

@executor_function
def get_image_hash(image: Image.Image, *, resize: Optional[Tuple[int, int]] = None) -> ImageHash:
    """
    Get an ImageHash from the image
    Resize is included because of how offten it's used with Hashing
    If resize is None the image is not resized
    :param image: The base Image
    :param resize: Tuple of size to resize to, defaults to None (see above)
    :return: The ImageHash object of this Image
    """
    if resize:
        image = image.resize(resize)

    return phash(image)


WallifyFactors = namedtuple('WallifyFactors', 'image_size wall_size emoji_size')


def get_wallify_factors(image_size: Tuple[int, int], wall_size: Tuple[int, int]) -> WallifyFactors:
    img_width, img_height = image_size
    wall_width, wall_height = wall_size

    emoji_width = img_width // wall_width
    emoji_height = img_height // wall_height

    new_width = (img_width // emoji_width) * emoji_width
    new_height = (img_height // emoji_height) * emoji_height

    num_of_columns = new_width // emoji_width
    num_of_rows = new_height // emoji_height

    return WallifyFactors(
        image_size=(new_width, new_height),
        wall_size=(num_of_rows, num_of_columns),
        emoji_size=(emoji_width, emoji_height)
    )


# Todo: test how long this takes to run (need to be under a second with up to 10, 10)
def get_wallify_example_file(wall_size: Tuple[int, int], name: str = None) -> BytesIO:
    num_of_rows, num_of_columns = wall_size

    text = '```\n'
    for row in range(num_of_rows):
        for column in range(num_of_columns):
            place = (num_of_columns * row) + column
            if name:
                text += f':{name}_{place}:'
            else:
                text += f':{place}:'

        text += '\n'
    text += '\n```'

    file_bytes = bytes(text, 'utf-8')

    file = BytesIO(file_bytes)

    return file

# Image manipulating

@executor_function
def wallify_image(image: Image.Image, width: int, height: int, *, name: str = None) -> Tuple[list, BytesIO]:
    """
    Wallify an image
    :param image: The base Image
    :param width: Width of the wall (Number of images)
    :param height: Height of the Wall (Number of images)
    :param name: Name to use in example file, defaults to None (uses '_')
    :return: Tuple of a list of Image and the example file
    """
    images = []

    factors = get_wallify_factors(image.size, (width, height))

    (new_width, new_height), (num_of_rows, num_of_columns), (image_width, image_height) = factors

    image = image.resize((new_width, new_height))

    for row in range(num_of_rows):
        for column in range(num_of_columns):
            images.append(image.crop((
                column * image_width,
                row * image_height,
                (column * image_width) + image_width,
                (row * image_height) + image_height
            )))

    wallify_example = get_wallify_example_file((num_of_rows, num_of_columns), name)

    return images, wallify_example


@executor_function
def wallify_gif_image(image: Image.Image, width: int, height: int, *, name: str = None) -> Tuple[list, BytesIO]:
    """
    Wallify a gif image
    :param image: The base Image
    :param width: Width of the wall (Number of images)
    :param height: Height of the Wall (Number of images)
    :param name: Name to use in example file, defaults to None (uses '_')
    :return: Tuple of a list of Image frames and the example file
    """
    images = []

    factors = get_wallify_factors(image.size, (width, height))

    (new_width, new_height), (num_of_rows, num_of_columns), (emoji_width, emoji_height) = factors

    for row in range(num_of_rows):
        for column in range(num_of_columns):
            frames = []

            for page in ImageSequence.Iterator(image):
                page = page.resize((new_width, new_height))
                frames.append(page.crop((
                    column * emoji_width,
                    row * emoji_height,
                    (column * emoji_width) + emoji_width,
                    (row * emoji_height) + emoji_height
                )))

            images.append(frames)

    wallify_example = get_wallify_example_file((num_of_rows, num_of_columns), name)

    return images, wallify_example


@executor_function
def shuffle_image(image: Image.Image, *, degree=1000) -> Image.Image:
    """
    Randomizes the pixles of an image [degree] times
    :param image: Image to randomize
    :param degree: Times to randomize, defaults to 1000
    :return: The randomized Image
    """
    array = image.load()

    def random_cord():
        return randint(0, image.size[0]), randint(0, image.size[1])

    for i in range(degree):
        x1, y1 = random_cord()
        x2, y2 = random_cord()

        array[x1, y1], array[x2, y2] = array[x2, y2], array[x1, y1]

    return image


@executor_function
def difference_image(image1: Image.Image, image2: Image.Image) -> Image.Image:
    """
    Executor alias for ImageChops.difference
    :param image1: Base image
    :param image2: Image to compare to
    :return: Composite Image of differences
    """
    return ImageChops.difference(image1, image2)
