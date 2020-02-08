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
from discord.ext import commands, menus


class DCMenuPages(menus.MenuPages):

    def __init__(self, source, **kwargs):
        super().__init__(source, **kwargs)

    def skip_two_or_less(self):
        max_pages = self._source.get_max_pages()
        if max_pages is None:
            return True
        return max_pages <= 2

    def skip_only_one_page(self):
        max_pages = self._source.get_max_pages()
        if max_pages is None:
            return True
        return max_pages <= 1

    def skip_one_or_two(self):
        return self.skip_only_one_page() or self.skip_two_or_less()

    @menus.button('\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f',
                  skip_if=skip_one_or_two)
    async def go_to_first_page(self, payload):
        """go to the first page"""
        await self.show_page(0)

    @menus.button('\N{BLACK LEFT-POINTING TRIANGLE}\ufe0f',
                  skip_if=skip_only_one_page)
    async def go_to_previous_page(self, payload):
        """go to the previous page"""
        await self.show_checked_page(self.current_page - 1)

    @menus.button('\N{BLACK RIGHT-POINTING TRIANGLE}\ufe0f',
                  skip_if=skip_only_one_page)
    async def go_to_next_page(self, payload):
        """go to the next page"""
        await self.show_checked_page(self.current_page + 1)

    @menus.button('\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f',
                  skip_if=skip_one_or_two)
    async def go_to_last_page(self, payload):
        """go to the last page"""
        # The call here is safe because it's guarded by skip_if
        await self.show_page(self._source.get_max_pages() - 1)

    @menus.button('\N{BLACK SQUARE FOR STOP}\ufe0f',
                  skip_if=skip_only_one_page)
    async def stop_pages(self, payload):
        """stops the pagination session."""
        self.stop()


class NormalPageSource(menus.ListPageSource):

    def __init__(self, entries):
        super().__init__(entries, per_page=1)

    async def format_page(self, menu, page):
        return page


# I should probably pr these changes but idk if this property thing
# is the correct way to do it so /shrug also the None thing looks dumb
class FixedNonePaginator(commands.Paginator):

    @property
    def _max_size_factor(self):
        if self.prefix is not None and self.suffix is not None:
            return 2
        elif self.prefix is not None or self.suffix is not None:
            return 1
        else:
            return 0

    def add_line(self, line='', *, empty=False):
        max_page_size = self.max_size - self._prefix_len - self._suffix_len - self._max_size_factor
        if len(line) > max_page_size:
            raise RuntimeError('Line exceeds maximum page size %s' % max_page_size)

        if self._count + len(line) + (0 if self.suffix is None else 1) > self.max_size - self._suffix_len:
            self.close_page()

        self._count += len(line) + 1
        self._current_page.append(line)

        if empty:
            self._current_page.append('')
            self._count += 1


# Modified from https://github.com/Gorialis/jishaku/blob/master/jishaku/paginators.py#L322
# (c) 2020 Devon (Gorialis) R
# This isn't a subclass to deal with jishaku.flags
class PartitionPaginator(FixedNonePaginator):
    """
    Version of WrappedPaginator that uses str.rpartition
    """

    def __init__(self, *args, wrap_on=('\n', ' '), include_wrapped=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.wrap_on = wrap_on
        self.include_wrapped = include_wrapped

    def add_line(self, line='', *, empty=False):
        true_max_size = self.max_size - self._prefix_len - self._suffix_len - self._max_size_factor

        while len(line) > true_max_size:
            search_string = line[0:true_max_size]
            line = line[true_max_size:]
            wrapped = False

            for delimiter in self.wrap_on:

                partition = search_string.rpartition(delimiter)

                if len(partition[0]) > 0:
                    wrapped = True

                    if self.include_wrapped:
                        super().add_line(partition[0] + partition[1], empty=empty)
                    else:
                        super().add_line(partition[0], empty=empty)

                    line = partition[2] + line

            if not wrapped:
                super().add_line(search_string, empty=empty)

        if len(line) > 0:
            super().add_line(line, empty=empty)


class PrologPaginator(FixedNonePaginator):

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
                self.add_header(str(key))
                self.recursively_add_dictonary(value)
            else:
                self.add_key_value_pair(str(key), str(value))

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
        self.add_line(f"{capwords(key):{self.align_option}{self.align_places}.{self.align_places}} :: "
                      f"{capwords(value)}")


class BreakPaginator(FixedNonePaginator):
    """
    Breaks lines up to fit in the paginator
    """

    def add_line(self, line='', *, empty=False):
        max_page_size = self.max_size - self._prefix_len - self._suffix_len - - self._max_size_factor

        for wrapped in wrap(line, max_page_size):
            super().add_line(wrapped, empty=empty)


class EmbedDictPaginator(FixedNonePaginator):

    def __init__(self, title: str = None, max_fields: int = 25):
        """
        A paginator for dicts of Embed fields
        :param title: Title of Embeds, defaults to Empty
        :param max_fields: Max number of fields must be <= 25
        """
        if not (0 <= max_fields <= 25):
            raise ValueError("max_fields must be between 0 and 25.")
        self.title = title or discord.Embed.Empty
        self.max_fields = max_fields
        super().__init__()

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
