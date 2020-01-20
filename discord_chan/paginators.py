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

from string import capwords
from textwrap import wrap

import discord
from discord.ext import commands
from jishaku.paginators import PaginatorInterface, WrappedPaginator


# Todo: pr fixing None prefix and suffix for paginators again Help.py 134 and 138 (check your local install)
# Todo: make sure this works perfectly with prefixes and suffix interchangeably being None
# from discord_chan import PartitionPaginator as pp; x = pp(prefix=None, suffix=None, wrap_on=('o', ), max_size=10)

class PartitionPaginator(WrappedPaginator):
    """
    Subclass of WrappedPaginator that uses str.rpartition
    """

    def __init__(self, *args, break_line_on_unwrapable=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.break_line_on_unwrapable = break_line_on_unwrapable

    # Todo: remove debug prints before master push
    def add_line(self, line='', *, empty=False):
        true_max_size = self.max_size - self._prefix_len - self._suffix_len  # - self._max_size_factor
        # print(f'{true_max_size=}')

        while len(line) > true_max_size:
            # print('')
            # print('top of while')
            search_string = line[0:true_max_size]
            line = line[true_max_size:]
            wrapped = False
            # print(f'{search_string=}')
            # print(f'{line=}')

            for delimiter in self.wrap_on:

                partition = search_string.rpartition(delimiter)
                # print(f'{partition=}')

                if len(partition[0]) > 0:
                    wrapped = True

                    if self.include_wrapped:
                        # print('includewrap-adding %s' % partition[0] + partition[1])
                        super(WrappedPaginator, self).add_line(partition[0] + partition[1], empty=empty)
                    else:
                        # print(f'!includewrap-adding {partition[0]}')
                        super(WrappedPaginator, self).add_line(partition[0], empty=empty)

                    line = partition[2] + line

            if not wrapped:
                # print(f'adding unwrapped {search_string=}')
                super(WrappedPaginator, self).add_line(search_string, empty=empty)

        if len(line) > 0:
            # print('at bottom add')
            # print(f'{line=}')
            super(WrappedPaginator, self).add_line(line, empty=empty)


class PrologPaginator(commands.Paginator):

    def __init__(self,
                 prefix: str = '```prolog',
                 suffix: str = '```',
                 max_size: int = 500,
                 align_option: str = '>',
                 align_places: int = 16):
        """
        :param align_option: How the options should be aligned, uses same
        symboles as f-strings (<, ^, >). Defaults to >
        :param align_places: To how many places the header and options should be aligned,
        defaults to 16
        """
        super().__init__(prefix, suffix, max_size)
        self.align_option = align_option
        self.align_places = align_places

    def recursively_add_dictonary(self, dictonary: dict):
        for key, value in dictonary.items():
            if isinstance(value, dict):
                self.add_header(key)
                self.recursively_add_dictonary(value)
            else:
                self.add_key_value_pair(key, value)

    def add_header(self, header: str):
        """
        :param header: The new header to add
        """
        header = f" {header} ".center(self.align_places * 2, '=')
        self.add_line(f"\n{capwords(str(header))}\n")

    def add_key_value_pair(self, key: str, value: str):
        """
        :param key: The key to add
        :param value: The value to add
        """
        self.add_line("{0:{align}{places}} :: {1}".format(
            capwords(str(key)),
            capwords(str(value)),
            align=self.align_option,
            places=self.align_places
        ))


class BreakPaginator(commands.Paginator):
    """
    Breaks lines up to fit in the paginator
    """

    def add_line(self, line='', *, empty=False):
        max_page_size = self.max_size - self._prefix_len - self._suffix_len - 2

        for wrapped in wrap(line, max_page_size):
            super().add_line(wrapped, empty=empty)


class EmbedDictPaginator(commands.Paginator):

    def __init__(self, title: str = None, max_fields: int = 25):
        """
        A paginator for for dicts of Embed fields
        :param title: Title of Embeds defaults to Empty
        :param max_fields: Max number of fields must be <= 25
        """
        super().__init__()
        if not (0 <= max_fields <= 25):
            raise ValueError("max_fields must be between 0 and 25.")

        self.title = title or discord.Embed.Empty
        self.max_fields = max_fields
        self.clear()

    @property
    def default_embed(self):
        return discord.Embed(title=self.title)

    @property
    def _prefix_len(self):
        return len(self.title)

    # noinspection PyAttributeOutsideInit
    def clear(self):
        """Clears the paginator to have no pages."""
        self._current_page = self.default_embed
        self._count = 0
        self._pages = []

    def add_line(self, line='', *, empty=False):
        raise NotImplementedError(self.add_line)

    def add_fields(self, data: dict):
        for name, value in data.items():
            self.add_field(name, value)

    def add_field(self, name: str, value: str):
        max_page_size = 6_000

        if len(name) > 256:
            raise RuntimeError('Name exceeds maximum field name size 256')
        elif len(value) > 1_024:
            raise RuntimeError('Value exceeds maximum field value size 1,024')

        if len(self._current_page) + len(name + value) > max_page_size:
            self.close_page()
        elif self._count >= self.max_fields:
            self.close_page()
        else:
            self._current_page.add_field(name=name, value=value, inline=False)
            self._count += 1

    # noinspection PyAttributeOutsideInit
    def close_page(self):
        """Prematurely terminate a page."""
        self._pages.append(self._current_page)
        self._current_page = self.default_embed
        self._count = 0

    def __len__(self):
        total = sum(len(p) for p in self._pages)
        return total

    @property
    def pages(self) -> list:
        """Returns the rendered list of pages."""
        if self._count > 0:
            self.close_page()
        return self._pages

    def __repr__(self):
        return f'<Paginator pages: {len(self._pages)} length: {len(self)} count: {self._count}>'


class EmbedDictInterface(PaginatorInterface):
    max_page_size = 25

    # noinspection PyProtectedMember
    @property
    def pages(self) -> list:
        """
        Returns the paginator's pages without prematurely closing the active page.
        """
        # protected access has to be permitted here to not close the paginator's pages

        # pylint: disable=protected-access
        paginator_pages = list(self.paginator._pages)
        if self.paginator._count > 0:
            paginator_pages.append(self.paginator._current_page)
        # pylint: enable=protected-access

        return paginator_pages

    @property
    def send_kwargs(self) -> dict:
        display_page = self.display_page
        page_num = f'Page {display_page + 1}/{self.page_count}'
        embed = self.pages[display_page].set_footer(text=page_num)
        return {'embed': embed}

    @property
    def page_size(self) -> int:
        return self.paginator.max_fields
