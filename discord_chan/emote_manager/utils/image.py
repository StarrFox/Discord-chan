# © 2018–2020 io mintz <io@mintz.cc>
#
# Emote Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Emote Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Emote Manager. If not, see <https://www.gnu.org/licenses/>.

import asyncio
import base64
import contextlib
import functools
import io
import typing
from concurrent.futures.thread import ThreadPoolExecutor

from loguru import logger

from . import errors

try:
    import wand.exceptions
    import wand.image
except (ImportError, OSError):
    logger.warning(
        "Failed to import wand.image. Image manipulation functions will be unavailable."
    )


# Modified from https://github.com/Gorialis/jishaku/blob/master/jishaku/functools.py#L19
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
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
def executor_function(sync_function: typing.Callable):
    @functools.wraps(sync_function)
    async def sync_wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        internal_function = functools.partial(sync_function, *args, **kwargs)

        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, internal_function)

    return sync_wrapper


@executor_function
def resize_until_small(image_data: bytes) -> bytes:
    """If the image_data is bigger than 256KB, resize it until it's not."""
    # It's important that we only attempt to resize the image when we have to,
    # ie when it exceeds the Discord limit of 256KiB.
    # Apparently some <256KiB images become larger when we attempt to resize them,
    # so resizing sometimes does more harm than good.
    image_data = io.BytesIO(image_data)
    max_resolution = 128  # pixels
    image_size = size(image_data)
    if image_size <= 256 * 2**10:
        return image_data.read()

    try:
        with wand.image.Image(blob=image_data) as original_image:
            while True:
                logger.debug("image size too big (%s bytes)", image_size)
                logger.debug(
                    "attempting resize to at most%s*%s pixels",
                    max_resolution,
                    max_resolution,
                )

                with original_image.clone() as resized:
                    resized.transform(resize=f"{max_resolution}x{max_resolution}")
                    image_size = len(resized.make_blob())
                    if (
                        image_size <= 256 * 2**10 or max_resolution < 32
                    ):  # don't resize past 256KiB or 32×32
                        image_data.truncate(0)
                        image_data.seek(0)
                        resized.save(file=image_data)
                        image_data.seek(0)
                        break

                max_resolution //= 2
    except wand.exceptions.CoderError:
        raise errors.InvalidImageError
    else:
        return image_data.read()


@executor_function
def convert_to_gif(image_data: bytes) -> bytes:
    image_data = io.BytesIO(image_data)
    try:
        with wand.image.Image(blob=image_data) as orig, orig.convert(
            "gif"
        ) as converted:
            # discord tries to stop us from abusing animated gif slots by detecting single frame gifs
            # so make it two frames
            converted.sequence[0].delay = 0  # show the first frame forever
            converted.sequence.append(wand.image.Image(width=1, height=1))

            image_data.truncate(0)
            image_data.seek(0)
            converted.save(file=image_data)
            image_data.seek(0)
    except wand.exceptions.CoderError:
        raise errors.InvalidImageError
    else:
        return image_data.read()


def mime_type_for_image(data):
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xFF\xD8") and data.rstrip(b"\0").endswith(b"\xFF\xD9"):
        return "image/jpeg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    raise errors.InvalidImageError


def image_to_base64_url(data):
    fmt = "data:{mime};base64,{data}"
    mime = mime_type_for_image(data)
    b64 = base64.b64encode(data).decode("ascii")
    return fmt.format(mime=mime, data=b64)


def size(fp):
    """return the size, in bytes, of the data a file-like object represents"""
    with preserve_position(fp):
        fp.seek(0, io.SEEK_END)
        return fp.tell()


class preserve_position(contextlib.AbstractContextManager):
    def __init__(self, fp):
        self.fp = fp
        self.old_pos = fp.tell()

    def __exit__(self, *excinfo):
        self.fp.seek(self.old_pos)
