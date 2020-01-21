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

from discord.ext import commands


class BadFormatArgument(commands.BadArgument):
    pass


class BadBetweenArgument(commands.BadArgument):
    pass

class BadNumberArgument(commands.BadArgument):
    pass

class ImageFormatConverter(commands.Converter):

    async def convert(self, ctx, argument):
        if argument in ('png', 'gif', 'jpeg', 'webp'):
            return argument
        else:
            raise BadFormatArgument('{} is not a valid image format.'.format(argument))


class BetweenConverter(commands.Converter):

    def __init__(self, num1, num2):
        self.num1 = num1
        self.num2 = num2

    async def convert(self, ctx, argument):
        try:
            argument = int(argument)
        except ValueError:
            raise BadNumberArgument('{} is not a valid number.'.format(argument))
        if self.num1 <= argument <= self.num2:
            return argument

        raise BadBetweenArgument('{} is not between {} and {}'.format(argument, self.num1, self.num2))
