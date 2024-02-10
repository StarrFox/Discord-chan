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

"""various utilities for use within the bot"""

import asyncio
from typing import Awaitable

import aiohttp
import discord
from discord.ext import commands


def format_user(bot: commands.Bot, id: int, *, mention: bool = False):
    """Format a user ID for human readable display"""
    user = bot.get_user(id)
    if user is None:
        return f"Unknown user with ID {id}"
    # not mention: @null byte#8191 (140516693242937345)
    # mention: <@140516693242937345> (null byte#8191)
    # this allows people to still see the username and discrim
    # if they don't share a server with that user
    if mention:
        return f"{user.mention} (@{user})"
    else:
        return f"@{user} ({user.id})"


def format_http_exception(exception: discord.HTTPException):
    """Formats a discord.HTTPException for relaying to the user.
    Sample return value:

    BAD REQUEST (status code: 400):
    Invalid Form Body
    In image: File cannot be larger than 256 kb.
    """

    # why is the name different between response types?
    if isinstance(exception.response, aiohttp.ClientResponse):
        status_code = exception.response.status
    else:
        status_code = exception.response.status_code

    return (
        f"{exception.response.reason} (status code: {status_code}):"
        f"\n{exception.text}"
    )


def strip_angle_brackets(string: str):
    """Strip leading < and trailing > from a string.
    Useful if a user sends you a url like <this> to avoid embeds, or to convert emotes to reactions.
    """
    if string.startswith("<") and string.endswith(">"):
        return string[1:-1]
    return string


async def gather_or_cancel(*awaitables: Awaitable):
    """run the awaitables in the sequence concurrently. If any of them raise an exception,
    propagate the first exception raised and cancel all other awaitables.
    """
    gather_task = asyncio.gather(*awaitables)
    try:
        return await gather_task
    except asyncio.CancelledError:
        raise
    except:
        gather_task.cancel()
        raise
