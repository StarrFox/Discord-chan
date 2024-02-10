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
import collections
import contextlib
import io
import operator
import posixpath
import re
import warnings
import weakref
import zipfile
from typing import Literal

import aiohttp
import discord
import humanize
from discord.ext import commands

import discord_chan.emote_manager.utils as utils
import discord_chan.emote_manager.utils.image as utils_image
from discord_chan.emote_manager.utils import errors
from discord_chan.emote_manager.utils.paginator import ListPaginator


# guilds can have duplicate emotes, so let us create zips to match
warnings.filterwarnings(
    "ignore", module="zipfile", category=UserWarning, message=r"^Duplicate name: .*$"
)


class UserCancelledError(commands.UserInputError):
    pass


LICENSE_NOTICE = """
Edited version of Emote Manager for use in lambadanator

Original license:
© 2018-2020 lambda#0987

Emote Manager is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

Emote Manager is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You may find a copy of the GNU Affero General Public License at
https://github.com/EmoteBot/EmoteManager/blob/master/LICENSE.md.
The rest of the source code is also there.
"""


class EmoteManager(commands.Cog):
    IMAGE_MIMETYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}
    TAR_MIMETYPES = {"application/x-tar"}
    ZIP_MIMETYPES = {
        "application/zip",
        "application/octet-stream",
        "application/x-zip-compressed",
        "multipart/x-zip",
    }
    ARCHIVE_MIMETYPES = TAR_MIMETYPES | ZIP_MIMETYPES
    ZIP_OVERHEAD_BYTES = 30

    def __init__(self, bot):
        self.bot = bot

        self.http = aiohttp.ClientSession(
            loop=self.bot.loop,
            timeout=60,
        )

        # keep track of paginators so we can end them when the cog is unloaded
        self.paginators = weakref.WeakSet()

    async def cog_unload(self):
        await self.http.close()

        for paginator in self.paginators:
            await paginator.stop()

    async def cog_check(self, context):
        # only allow in guilds
        if context.guild is None:
            raise commands.NoPrivateMessage()

        return True

    @commands.group(invoke_without_command=True)
    async def em(self, context):
        """
        Base command for emote manager commands
        """
        await context.send_help("em")

    @em.command()
    async def copyright(self, context):
        """
        Tells you about the copyright license for this extension
        """
        await context.send(LICENSE_NOTICE)

    @em.command(usage="[name] <image URL or custom emote>")
    @commands.has_permissions(manage_expressions=True)
    @commands.bot_has_permissions(manage_expressions=True)
    async def add(self, context: commands.Context, *args: str):
        """Add a new emote to this server.

        You can use it like this:
        `add :thonkang:` (if you already have that emote)
        `add rollsafe https://image.noelshack.com/fichiers/2017/06/1486495269-rollsafe.png`
        `add speedtest <https://cdn.discordapp.com/emojis/379127000398430219.png>`

        With a file attachment:
        `add name` will upload a new emote using the first attachment as the image and call it `name`
        `add` will upload a new emote using the first attachment as the image,
        and its filename as the name
        """
        name, url = self.parse_add_command_args(context, args)
        async with context.typing():
            message = await self.add_safe(context, name, url, context.message.author.id)
        await context.send(message)

    @em.command(name="add-these")
    @commands.has_permissions(manage_expressions=True)
    @commands.bot_has_permissions(manage_expressions=True)
    async def add_these(self, context: commands.Context, *emotes):
        """Add a bunch of custom emotes"""

        ran = False
        # we could use *emotes: discord.PartialEmoji here but that would require spaces between each emote.
        # and would fail if any arguments were not valid emotes
        for match in re.finditer(utils.emote.RE_CUSTOM_EMOTE, "".join(emotes)):
            ran = True
            animated, name, id = match.groups()
            image_url = utils.emote.url(id, animated=bool(animated))
            async with context.typing():
                message = await self.add_safe(
                    context, name, image_url, context.author.id
                )
                await context.send(message)

        if not ran:
            return await context.send("Error: no custom emotes were provided")

        await context.message.add_reaction("✅")

    @classmethod
    def parse_add_command_args(cls, context: commands.Context, args: tuple[str, ...]):
        if context.message.attachments:
            return cls.parse_add_command_attachment(context, args)

        elif len(args) == 1:
            match: re.Match[str] | None = utils.emote.RE_CUSTOM_EMOTE.match(args[0])
            if match is None:
                raise commands.BadArgument(
                    "Error: I expected a custom emote as the first argument, "
                    "but I got something else. "
                    "If you're trying to add an emote using an image URL, "
                    "you need to provide a name as the first argument, like this:\n"
                    "`{}add NAME_HERE URL_HERE`".format(context.prefix)
                )
            else:
                animated, name, id = match.groups()
                url = utils.emote.url(id, animated=bool(animated))

            return name, url

        elif len(args) >= 2:
            name = args[0]
            match = utils.emote.RE_CUSTOM_EMOTE.match(args[1])
            if match is None:
                url = utils.strip_angle_brackets(args[1])
            else:
                url = utils.emote.url(match["id"], animated=bool(match["animated"]))

            return name, url

        raise commands.BadArgument("Your message had no emotes and no name!")

    @classmethod
    def parse_add_command_attachment(cls, context: commands.Context, args):
        attachment = context.message.attachments[0]
        name = cls.format_emote_filename("".join(args) if args else attachment.filename)
        url = attachment.url

        return name, url

    @staticmethod
    def format_emote_filename(filename) -> str:
        """format a filename to an emote name as discord does when you upload an emote image"""
        left, sep, right = posixpath.splitext(filename)[0].rpartition("-")
        return (left or right).replace(" ", "")

    @em.command()
    @commands.bot_has_permissions(attach_files=True)
    async def export(
        self,
        context: commands.Context,
        image_type: Literal["all", "static", "animated"] = "all",
    ):
        """Export all emotes from this server to a zip file, suitable for use with the import command.

        If “animated” is provided, only include animated emotes.
        If “static” is provided, only include static emotes.
        Otherwise, or if “all” is provided, export all emotes.

        This command requires the “attach files” permission.
        """
        match image_type:
            case "all":
                emote_filter = lambda _: True
            case "static":
                emote_filter = lambda e: not e.animated
            case "animated":
                emote_filter = lambda e: e.animated

        emotes = list(filter(emote_filter, context.guild.emojis))  # type: ignore

        if not emotes:
            raise commands.BadArgument(
                "No emotes of that type were found in this server"
            )

        async with context.typing():
            async for zip_file in self.archive_emotes(context, emotes):
                await context.send(file=zip_file)

    async def archive_emotes(self, context: commands.Context, emotes):
        filesize_limit = context.guild.filesize_limit  # type: ignore
        discrims = collections.defaultdict(int)
        downloaded = collections.deque()

        # noinspection PyShadowingNames
        async def download(emote):
            # don't put two files in the zip with the same name
            discrims[emote.name] += 1
            discrim = discrims[emote.name]
            if discrim == 1:
                name = emote.name
            else:
                name = f"{emote.name}-{discrim}"

            name = f'{name}.{"gif" if emote.animated else "png"}'

            # place some level of trust on discord's CDN to actually give us images
            data = await self.fetch_safe(str(emote.url))
            if type(data) is str:  # error case
                await context.send(f"{emote}: {data}")
                return

            est_zip_overhead = len(name) + self.ZIP_OVERHEAD_BYTES
            est_size_in_zip = est_zip_overhead + len(data)
            if est_size_in_zip >= filesize_limit:
                self.bot.loop.create_task(
                    context.send(
                        f"{emote} could not be added because it alone would exceed the file size limit"
                    )
                )
                return

            downloaded.append((name, emote.created_at, est_size_in_zip, data))

        await utils.gather_or_cancel(*map(download, emotes))

        count = 1
        while True:
            out = io.BytesIO()
            with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as _zip:
                while True:
                    try:
                        item = downloaded.popleft()
                    except IndexError:
                        break

                    name, created_at, est_size, image_data = item

                    if out.tell() + est_size >= filesize_limit:
                        # adding this emote would bring us over the file size limit
                        downloaded.appendleft(item)
                        break

                    zinfo = zipfile.ZipInfo(name, date_time=created_at.timetuple()[:6])
                    _zip.writestr(zinfo, image_data)

                if out.tell() == 0:
                    # no emotes were written
                    break

            out.seek(0)
            yield discord.File(out, f"emotes-{context.guild.id}-{count}.zip")  # type: ignore
            count += 1

    @em.command(
        name="import", aliases=["add-zip", "add-tar", "add-from-zip", "add-from-tar"]
    )
    @commands.has_permissions(manage_expressions=True)
    @commands.bot_has_permissions(manage_expressions=True)
    async def import_(self, context: commands.Context, url=None):
        """Add several emotes from a .zip or .tar archive.

        You may either pass a URL to an archive or upload one as an attachment.
        All valid GIF, PNG, and JPEG files in the archive will be uploaded as emotes.
        The rest will be ignored.
        """
        if url and context.message.attachments:
            raise commands.BadArgument(
                "Either a URL or an attachment must be given, not both"
            )
        if not url and not context.message.attachments:
            raise commands.BadArgument("A URL or attachment must be given")

        url = url or context.message.attachments[0].url
        async with context.typing():
            archive = await self.fetch_safe(url, valid_mimetypes=self.ARCHIVE_MIMETYPES)
        if type(archive) is str:  # error case
            await context.send(archive)
            return

        await self.add_from_archive(context, archive)
        with contextlib.suppress(discord.HTTPException):
            # so they know when we're done
            await context.message.add_reaction("✅")

    async def add_from_archive(self, context: commands.Context, archive):
        limit = (
            50_000_000  # prevent someone from trying to make a giant compressed file
        )
        async for name, img, error in utils.archive.extract_async(
            io.BytesIO(archive), size_limit=limit
        ):
            try:
                utils_image.mime_type_for_image(img)
            except errors.InvalidImageError:
                continue
            if error is None:
                name = self.format_emote_filename(posixpath.basename(name))
                async with context.typing():
                    # we can ignore the type here because content should be set if error is None
                    message = await self.add_safe_bytes(
                        context, name, context.author.id, img  # type: ignore
                    )
                await context.send(message)
                continue

            if isinstance(error, errors.FileTooBigError):
                await context.send(
                    f"{name}: file too big. "
                    f"The limit is {humanize.naturalsize(error.limit)} "
                    f"but this file is {humanize.naturalsize(error.size)}"
                )
                continue

            await context.send(f"{name}: {error}")

    async def add_safe(
        self, context: commands.Context, name, url, author_id, *, reason=None
    ):
        """Try to add an emote. Returns a string that should be sent to the user"""
        try:
            image_data = await self.fetch_safe(url)
        except errors.InvalidFileError:
            raise errors.InvalidImageError

        if isinstance(image_data, str):  # error case
            return image_data
        return await self.add_safe_bytes(
            context, name, author_id, image_data, reason=reason
        )

    async def fetch_safe(self, url, valid_mimetypes=None, *, validate_headers=False):
        """Try to fetch a URL. On error return a string that should be sent to the user"""
        try:
            return await self.fetch(
                url, valid_mimetypes=valid_mimetypes, validate_headers=validate_headers
            )
        except asyncio.TimeoutError:
            return "Error: retrieving the image took too long"
        except ValueError:
            return "Error: Invalid URL"
        except aiohttp.ClientResponseError as exc:
            raise errors.HTTPException(exc.status)

    async def add_safe_bytes(
        self,
        context: commands.Context,
        name,
        author_id,
        image_data: bytes,
        *,
        reason=None,
    ):
        """Try to add an emote from bytes. On error, return a string that should be sent to the user.

        If the image is static and there are not enough free static slots, convert the image to a gif instead.
        """
        counts = collections.Counter(
            map(operator.attrgetter("animated"), context.guild.emojis)  # type: ignore
        )
        # >= rather than == because there are sneaky ways to exceed the limit
        if (
            counts[False] >= context.guild.emoji_limit  # type: ignore
            and counts[True] >= context.guild.emoji_limit  # type: ignore
        ):
            # we raise instead of returning a string in order to abort commands that run this function in a loop
            raise commands.UserInputError("This server is out of emote slots")

        static = utils_image.mime_type_for_image(image_data) != "image/gif"
        converted = False
        if static and counts[False] >= context.guild.emoji_limit:  # type: ignore
            image_data = await utils_image.convert_to_gif(image_data)
            converted = True

        try:
            emote = await self.create_emote_from_bytes(
                context.guild, name, author_id, image_data, reason=reason
            )
        # https://discordpy.readthedocs.io/en/stable/migrating.html?highlight=invalidargument#removal-of-invalidargument-exception
        # I can't be bothered to figure out which it should be
        except (TypeError, ValueError):
            return discord.utils.escape_mentions(
                f"{name}: The file supplied was not a valid GIF, PNG, JPEG, or WEBP file"
            )
        except discord.HTTPException as ex:
            return discord.utils.escape_mentions(
                f"{name}: An error occurred while creating the the emote:\n"
                + utils.format_http_exception(ex)
            )
        s = f"Emote {emote} successfully created"
        return s + " as a GIF" if converted else s

    # noinspection PyDefaultArgument
    async def fetch(
        self, url, valid_mimetypes=IMAGE_MIMETYPES, *, validate_headers=True
    ):
        valid_mimetypes = valid_mimetypes or self.IMAGE_MIMETYPES

        def _validate_headers(response: aiohttp.ClientResponse):
            response.raise_for_status()
            # some dumb servers also send '; charset=UTF-8' which we should ignore
            # TODO: preserve this behavior with a new library (cgi was depreciated)
            # mimetype, options = cgi.parse_header(
            #     response.headers.get("Content-Type", "")
            # )
            mimetype = response.content_type
            if mimetype not in valid_mimetypes:
                raise errors.InvalidFileError

        async def validate(request) -> bytes:
            try:
                async with request as response:
                    _validate_headers(response)
                    return await response.read()
            except aiohttp.ClientResponseError:
                raise
            except aiohttp.ClientError as exc:
                raise errors.EmoteManagerError(
                    f"An error occurred while retrieving the file: {exc}"
                )

        if validate_headers:
            await validate(self.http.head(url, timeout=10))
        return await validate(self.http.get(url))

    async def create_emote_from_bytes(
        self, guild, name, author_id, image_data: bytes, *, reason=None
    ):
        image_data = await utils_image.resize_until_small(image_data)
        if reason is None:
            reason = f"Created by {utils.format_user(self.bot, author_id)}"
        return await guild.create_custom_emoji(
            name=name, image=image_data, reason=reason
        )

    @em.command(aliases=("delete", "rm"))
    @commands.has_permissions(manage_expressions=True)
    @commands.bot_has_permissions(manage_expressions=True)
    async def remove(self, context: commands.Context, emote, *emotes):
        """Remove an emote from this server.

        emotes: the name of an emote or of one or more emotes you'd like to remove.
        """
        if not emotes:
            emote = await self.parse_emote(context, emote)
            await emote.delete(
                reason=f"Removed by {utils.format_user(self.bot, context.author.id)}"
            )
            await context.send(rf"Emote \:{emote.name}: successfully removed")
        else:
            for emote in (emote,) + emotes:
                await context.invoke(self.remove, emote)
            with contextlib.suppress(discord.HTTPException):
                await context.message.add_reaction("✅")

    @em.command(aliases=("mv",))
    @commands.has_permissions(manage_expressions=True)
    @commands.bot_has_permissions(manage_expressions=True)
    async def rename(self, context: commands.Context, old, new_name):
        """Rename an emote on this server.

        old: the name of the emote to rename, or the emote itself
        new_name: what you'd like to rename it to
        """
        emote = await self.parse_emote(context, old)
        try:
            await emote.edit(
                name=new_name,
                reason=f"Renamed by {utils.format_user(self.bot, context.author.id)}",
            )
        except discord.HTTPException as ex:
            return await context.send(
                "An error occurred while renaming the emote:\n"
                + utils.format_http_exception(ex)
            )

        await context.send(rf"Emote successfully renamed to \:{new_name}:")

    @em.command(aliases=("ls", "dir"))
    async def list(
        self,
        context: commands.Context,
        image_type: Literal["all", "static", "animated"] = "all",
    ):
        """A list of all emotes on this server.

        The list shows each emote and its raw form.

        If "animated" is provided, only show animated emotes.
        If "static" is provided, only show static emotes.
        If “all” is provided, show all emotes.
        """
        match image_type:
            case "all":
                emote_filter = lambda _: True
            case "static":
                emote_filter = lambda e: not e.animated
            case "animated":
                emote_filter = lambda e: e.animated

        emotes = sorted(
            filter(emote_filter, context.guild.emojis), key=lambda e: e.name.lower()  # type: ignore
        )

        processed = []
        for emote in emotes:
            raw = str(emote).replace(":", r"\:")
            processed.append(f"{emote} {raw}")

        paginator = ListPaginator(context, processed)
        self.paginators.add(paginator)
        await paginator.begin()

    @em.command(aliases=["status"])
    async def stats(self, context):
        """The current number of animated and static emotes relative to the limits"""
        emote_limit = context.guild.emoji_limit

        static_emotes = animated_emotes = total_emotes = 0
        for emote in context.guild.emojis:
            if emote.animated:
                animated_emotes += 1
            else:
                static_emotes += 1

            total_emotes += 1

        percent_static = round((static_emotes / emote_limit) * 100, 2)
        percent_animated = round((animated_emotes / emote_limit) * 100, 2)

        static_left = emote_limit - static_emotes
        animated_left = emote_limit - animated_emotes

        await context.send(
            f"Static emotes: **{static_emotes} / {emote_limit}** ({static_left} left, {percent_static}% full)\n"
            f"Animated emotes: **{animated_emotes} / {emote_limit}** ({animated_left} left, {percent_animated}% full)\n"
            f"Total: **{total_emotes} / {emote_limit * 2}**"
        )

    @em.command(aliases=["embiggen"])
    async def big(self, context: commands.Context, emote):
        """Shows the original image for the given emote.

        emote: the emote to embiggen
        """
        emote = await self.parse_emote(context, emote)
        await context.send(f"{emote.name}: {emote.url}")

    async def parse_emote(self, context: commands.Context, name_or_emote):
        match = utils.emote.RE_CUSTOM_EMOTE.match(name_or_emote)
        if match:
            id = int(match.group("id"))
            emote = discord.utils.get(context.guild.emojis, id=id)  # type: ignore
            if emote:
                return emote
        name = name_or_emote
        return await self.disambiguate(context, name)

    async def disambiguate(self, context: commands.Context, name):
        name = name.strip(":")  # in case the user tries :foo: and foo is animated
        candidates = [
            e
            for e in context.guild.emojis  # type: ignore
            if e.name.lower() == name.lower() and e.require_colons
        ]
        if not candidates:
            raise errors.EmoteNotFoundError(name)

        if len(candidates) == 1:
            return candidates[0]

        message = ["Multiple emotes were found with that name. Which one do you mean?"]
        for i, emote in enumerate(candidates, 1):
            message.append(rf"{i}. {emote} (\:{emote.name}:)")

        await context.send("\n".join(message))

        # noinspection PyShadowingNames
        def check(message):
            try:
                int(message.content)
            except ValueError:
                return False
            else:
                return message.author == context.author

        try:
            message = await self.bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            raise commands.UserInputError("Sorry, you took too long. Try again")

        return candidates[int(message.content) - 1]


async def setup(bot):
    await bot.add_cog(EmoteManager(bot))
