import asyncio
import functools
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from tarfile import TarFile, TarInfo
from typing import NamedTuple, ParamSpec, TypeVar
import operator
import re

import aiohttp
from discord import File
from PIL import Image, ImageChops, ImageSequence, ImagePalette


try:
    import wand.image
except ImportError:
    wand = None


class ImageError(Exception):
    pass


class FileTooLarge(ImageError):
    pass


class InvalidImageType(ImageError):
    pass


SIMPLE_COLORS: dict[str, tuple[int, int, int]] = {
    "red": (0xFF, 0, 0),
    "green": (0, 0xFF, 0),
    "blue": (0, 0, 0xFF),
    "orange": (0xFF, 0xA5, 0),
    "brown": (0x96, 0x4B, 0),
    "yellow": (0xFF, 0xFF, 0),
    "purple": (0xA0, 0x20, 0xF0),
    "pink": (0xFF, 0xC0, 0xCB),
}


T = TypeVar("T")
P = ParamSpec("P")


# Modified from https://github.com/Gorialis/jishaku/blob/bf26bea3c1f86993fd75744de48bf52d4925521a/jishaku/functools.py#L22
# This license covers the below function
# MIT License
#
# Copyright (c) 2020 Devon (Gorialis) R
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
def executor_function(sync_function: Callable[P, T]):  # type: ignore
    @functools.wraps(sync_function)
    async def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        loop = asyncio.get_event_loop()
        internal_function = functools.partial(sync_function, *args, **kwargs)

        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, internal_function)

    return sync_wrapper


class TypedBytes(NamedTuple):
    file_bytes: bytes
    content_type: str


async def get_bytes(link: str, *, max_length: int = 100) -> TypedBytes:
    """
    Get bytes and content_type from a link
    :param link: URL to the file
    :param max_length: Max file size to download in MB
    :return: TypedBytes representing the bytes and content_type
    :raise FileTooLarge: If the file was beyond max_length
    """
    # Bytes *1000 -> kb *1000 -> MB
    max_length = round((max_length * 1000) * 1000)
    async with aiohttp.ClientSession().get(link) as response:
        # TODO: handle these
        response.raise_for_status()

        if response.content_length is None:
            raise ValueError("content_length was None")

        if response.content_length > max_length:
            raise FileTooLarge(
                f"{round((response.content_length / 1000) / 1000, 2)}mb is over max size of {(max_length / 1000 / 1000)}mb"
            )

        return TypedBytes(
            file_bytes=await response.read(), content_type=response.content_type
        )


_tenor_regex = re.compile(r'class="Gif"[^<]+<img src="([^"]+)"')


async def _get_inner_tenor_gif(link: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(link) as response:
            response.raise_for_status()

            text = await response.text()

    regex_match = _tenor_regex.search(text)

    if regex_match is None:
        raise InvalidImageType("Could not find any gifs in tenor link")

    return regex_match.group(1)


async def url_to_image(link: str) -> Image.Image:
    """
    Convence function to convert a link to a PIL Image
    :param link: The url of the image
    :return: Image representing the image
    :raises InvalidImage, FileTooLarge: PIL could not open the file
    """
    if link.startswith("https://tenor.com/"):
        link = await _get_inner_tenor_gif(link)

    image_bytes, content_type = await get_bytes(link, max_length=10)

    # TODO: get the exact formats the running PIL supports
    # Check before to try and save some memory
    if "image" not in content_type.lower():
        raise InvalidImageType(f"{content_type.lower()} is not a valid image type")

    file_obj = BytesIO(image_bytes)

    @executor_function
    def open_image(img):
        return Image.open(img)

    try:
        image = await open_image(file_obj)
    except OSError:
        # This should never get here
        raise InvalidImageType(f"{content_type.lower()} is not a valid image type")

    return image


@executor_function
def tarball_images(
    images: list[Image.Image] | list[list[Image.Image]],
    *,
    name: str | None = None,
    animated: bool = False,
    format: str = "png",
    extras: list[tuple[str, BytesIO]],
) -> BytesIO:
    fp = BytesIO()
    tar = TarFile(mode="w", fileobj=fp)

    # TODO: fix type checking
    for idx, image in enumerate(images):  # type: ignore
        f = BytesIO()
        if animated:
            image[0].save(f, format, append_images=image[1:], save_all=True, loop=0)  # type: ignore
        else:
            image: Image.Image
            image.save(f, format)

        f.seek(0)
        if name:
            info = TarInfo(f"{name}_{idx}.{format}")
        else:
            info = TarInfo(f"{idx}.{format}")
        info.size = len(f.getbuffer())
        tar.addfile(info, fileobj=f)

    for extra in extras:
        info = TarInfo(extra[0] or "_.txt")
        info.size = len(extra[1].getbuffer())
        tar.addfile(info, fileobj=extra[1])

    fp.seek(0)
    return fp


@executor_function
def image_to_file(
    image: Image.Image, filename: str | None = None, format: str = "png"
) -> File:
    """
    Saves an image into a :class:discord.File
    :param image: The image to save
    :param filename: The filename to use
    :param format:
    :return: The File ready to send
    """
    buffer = BytesIO()

    image.save(buffer, format)
    buffer.seek(0)

    return File(buffer, filename=filename)


class WallifyFactors(NamedTuple):
    image_size: tuple[int, int]
    wall_size: tuple[int, int]
    emoji_size: tuple[int, int]


def get_wallify_factors(
    image_size: tuple[int, int], wall_size: tuple[int, int]
) -> WallifyFactors:
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
        emoji_size=(emoji_width, emoji_height),
    )


def get_wallify_example_file(
    wall_size: tuple[int, int], name: str | None = None
) -> BytesIO:
    num_of_rows, num_of_columns = wall_size

    text = "```\n"
    for row in range(num_of_rows):
        for column in range(num_of_columns):
            place = (num_of_columns * row) + column
            if name:
                text += f":{name}_{place}:"
            else:
                text += f":{place}:"

        text += "\n"
    text += "\n```"

    file_bytes = bytes(text, "utf-8")
    file = BytesIO(file_bytes)
    return file


@executor_function
def wallify_image(image: Image.Image, width: int, height: int) -> list[Image.Image]:
    """Wallify an image"""
    images: list[Image.Image] = []

    factors = get_wallify_factors(image.size, (width, height))

    (
        (new_width, new_height),
        (num_of_rows, num_of_columns),
        (image_width, image_height),
    ) = factors

    image = image.resize((new_width, new_height))

    for row in range(num_of_rows):
        for column in range(num_of_columns):
            images.append(
                image.crop(
                    (
                        column * image_width,
                        row * image_height,
                        (column * image_width) + image_width,
                        (row * image_height) + image_height,
                    )
                )
            )

    return images


@executor_function
def wallify_gif_image(
    image: Image.Image, width: int, height: int
) -> list[list[Image.Image]]:
    """Wallify a gif image"""
    images: list[list[Image.Image]] = []

    factors = get_wallify_factors(image.size, (width, height))

    (
        (new_width, new_height),
        (num_of_rows, num_of_columns),
        (emoji_width, emoji_height),
    ) = factors

    for row in range(num_of_rows):
        for column in range(num_of_columns):
            frames: list[Image.Image] = []

            for page in ImageSequence.Iterator(image):
                page = page.resize((new_width, new_height))
                frames.append(
                    page.crop(
                        (
                            column * emoji_width,
                            row * emoji_height,
                            (column * emoji_width) + emoji_width,
                            (row * emoji_height) + emoji_height,
                        )
                    )
                )

            images.append(frames)

    return images


def equalize_images(*images) -> list[Image.Image]:
    sorted_by_area = sorted(
        ((i, i.size[0] * i.size[1]) for i in images), key=lambda t: t[1]
    )

    base = sorted_by_area[0][0]
    equalized = [base]
    resize = base.size

    for area_tuple in sorted_by_area[1:]:
        image = area_tuple[0]

        if image.size == resize:
            equalized.append(image)

        else:
            equalized.append(image.resize(resize))

    return equalized


@executor_function
def difference_image(image1: Image.Image, image2: Image.Image) -> Image.Image:
    """Get the difference between two images

    Args:
        image1 (Image.Image): first image
        image2 (Image.Image): second image

    Returns:
        Image.Image: the image difference
    """
    images = []
    for image in (image1, image2):
        if image.mode == "RGB":
            images.append(image)

        else:
            images.append(image.convert("RGB"))

    equalized = equalize_images(*images)

    return ImageChops.difference(*equalized)


@executor_function
def grayscale_image(image: Image.Image) -> Image.Image:
    """Make an Image grayscale

    Args:
        image: The Image to convert

    Returns:
        The converted Image
    """
    return image.convert("L")


@executor_function
def monochomize_image(image: bytes, method: str = "kapur") -> BytesIO:
    """Make an image black and white

    Args:
        image: The Image to convert
        method: The method to use; one of kapur, otsu, or triangle. Defaults to "kapur".

    Raises:
        RuntimeError: If wand is not installed

    Returns:
        The converted Image
    """
    if wand is None:
        raise RuntimeError(
            "Attempted calling wand using function without wand installed"
        )

    with wand.image.Image(blob=image) as img:
        img.auto_threshold(method)  # otsu kapur triangle
        buffer = BytesIO()
        img.save(buffer)
        buffer.seek(0)
        return buffer


@executor_function
def get_image_colors(image: Image.Image) -> dict[float, tuple[int, int, int, int]]:
    # TODO: is this ever rgb?
    if image.mode != "RGBA":
        raise ValueError("Non-rgb image passed to get colors")

    image = image.quantize()

    # palette_index: RGBA
    palette: dict[int, tuple[int, int, int, int]] = {
        v: k for k, v in image.palette.colors.items()
    }

    colors: list[tuple[int, int, int]] | None = image.getcolors()  # type: ignore (we have the correct type)

    if colors is None:
        # This shouldn't happen because of the quantize
        raise RuntimeError("Colors was somehow None")

    total_pixels: int = operator.mul(*image.size)

    percented_colors = map(lambda color: (color[0] / total_pixels, *color[1:]), colors)
    sorted_colors = sorted(percented_colors, key=lambda x: x[0], reverse=True)

    # percent: RGBA
    color_map: dict[float, tuple[int, int, int, int]] = {
        k: palette[v] for k, v in sorted_colors
    }

    return color_map


# def _get_random_color() -> tuple[int, int, int]:
#     return (
#         random.randrange(0, 255),
#         random.randrange(0, 255),
#         random.randrange(0, 255)
#     )


# @executor_function
# def randomize_image_colors(image: Image.Image):
#     if image.mode == "RGBA":
#         image = image.quantize()

#     if image.mode != "P":
#         raise RuntimeError("Non-P image in randomize colors")

#     colors = image.palette.colors

#     new_colors: dict[tuple[int, int, int, int], int] = {}
#     for index in range(len(colors)):
#         new_colors[(*_get_random_color(), 255)] = index

#     image.palette.colors = new_colors

#     #print(image.palette.getdata())

#     image.putpalette(ImagePalette.random("P"))

#     image.show()

#     return image
