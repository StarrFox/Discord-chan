# -*- coding: utf-8 -*-
#  Copyright © 2020 StarrFox
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

from datetime import datetime
from enum import Enum

import discord
import humanize
from discord.ext import flags


class SnipeMode(Enum):
    edited = 0
    deleted = 1
    purged = 2

    def __str__(self):
        return self.name


class Snipe:

    def __init__(self, message: discord.Message, mode: SnipeMode):
        self.mode = mode
        self.id = message.id
        self.time = datetime.utcnow()
        self.author = message.author
        self.content = message.content
        self.channel = message.channel

    @property
    def readable_time(self) -> str:
        return humanize.naturaltime(datetime.utcnow() - self.time)

    def __repr__(self):
        return f"<Snipe author={self.author} channel={self.channel} time={self.time}>"

    def __str__(self):
        return f"[{self.mode}] {self.author} ({self.readable_time})"


def snipe_parser(func: flags.FlagCommand):
    """
    Decorator to add the snipe parser
    :param func: The FlagCommand to add the parser to
    :return: The new FlagCommand with the added parser
    """
    flags.add_flag('--authors', nargs='+', type=discord.Member)(func)
    flags.add_flag('--channel', type=discord.TextChannel)(func)
    flags.add_flag('--guild', '--server', action='store_true')(func)
    flags.add_flag('--before', type=int)(func)
    flags.add_flag('--after', type=int)(func)
    flags.add_flag('--list', action='store_true')(func)
    flags.add_flag('--mode', choices=('deleted', 'purged', 'edited'))(func)
    flags.add_flag('--contains', nargs='+')(func)
    flags.add_flag('index', nargs='?', default=0, type=int)(func)
    return func
