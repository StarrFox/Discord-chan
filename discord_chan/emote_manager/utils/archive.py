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
import tarfile
import zipfile
from collections.abc import AsyncGenerator, Generator
from typing import Iterable, NamedTuple, Optional, Tuple

from . import errors


class ArchiveInfo(NamedTuple):
    filename: str
    content: bytes | None
    error: Exception | None


def extract(archive, *, size_limit=None) -> Iterable[ArchiveInfo]:
    """
    extract a binary file-like object representing a zip or uncompressed tar archive, yielding filenames and contents.

    yields ArchiveInfo objects: (filename: str, content: typing.Optional[bytes], error: )
    if size_limit is not None and the size limit is exceeded, or for any other error, yield None for content
    on success, error will be None
    """

    try:
        yield from extract_zip(archive, size_limit=size_limit)
        return
    except zipfile.BadZipFile:
        pass
    finally:
        archive.seek(0)

    try:
        yield from extract_tar(archive, size_limit=size_limit)
    except tarfile.ReadError as exc:
        raise ValueError("not a valid zip or tar file") from exc
    finally:
        archive.seek(0)


def extract_zip(archive, *, size_limit=None) -> Generator[ArchiveInfo, object, None]:
    with zipfile.ZipFile(archive) as zip:
        members = [m for m in zip.infolist() if not m.is_dir()]
        for member in members:
            if size_limit is not None and member.file_size >= size_limit:
                yield ArchiveInfo(
                    filename=member.filename,
                    content=None,
                    error=errors.FileTooBigError(member.file_size, size_limit),
                )
                continue

            try:
                content = zip.open(member).read()
            except RuntimeError as exc:  # why no specific exceptions smh
                yield ArchiveInfo(filename=member.filename, content=None, error=exc)
            else:  # this else is required to avoid UnboundLocalError for some reason
                yield ArchiveInfo(filename=member.filename, content=content, error=None)


def extract_tar(archive, *, size_limit=None) -> Generator[ArchiveInfo, object, None]:
    with tarfile.open(fileobj=archive) as tar:
        members = [f for f in tar.getmembers() if f.isfile()]
        for member in members:
            if size_limit is not None and member.size >= size_limit:
                yield ArchiveInfo(
                    filename=member.name,
                    content=None,
                    error=errors.FileTooBigError(member.size, size_limit),
                )
                continue

            # type can be ignored here because the member is garenteed to be within the tar
            yield ArchiveInfo(
                member.name, content=tar.extractfile(member).read(), error=None  # type: ignore
            )


async def extract_async(archive, size_limit=None) -> AsyncGenerator[ArchiveInfo, None]:
    for x in extract(archive, size_limit=size_limit):
        yield await asyncio.sleep(0, x)
