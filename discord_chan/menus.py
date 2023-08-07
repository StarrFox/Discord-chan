from collections import namedtuple
from string import capwords
from typing import Sequence

import discord
from discord.ext import commands, menus

EmbedFieldProxy = namedtuple("EmbedFieldProxy", "name value inline")


class ConfirmationMenu(menus.Menu):
    def __init__(
        self,
        to_confirm: str | None = None,
        *,
        owner_id: int | None = None,
        send_kwargs=None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        if send_kwargs is None:
            send_kwargs = {}

        self.owner_id = owner_id
        self.send_kwargs = send_kwargs
        self.to_confirm = to_confirm
        self.response = False

    async def send_initial_message(
        self, ctx: commands.Context, channel: discord.TextChannel
    ):
        return await ctx.send(self.to_confirm or "\u200b", **self.send_kwargs)

    def reaction_check(self, payload):
        # these types can be ignored because this function is only run after .start has been called
        if payload.message_id != self.message.id:  # type: ignore
            return False

        if self.owner_id is not None:
            if payload.user_id not in (self.owner_id, self.bot.owner_id):  # type: ignore
                return False

        else:
            if payload.user_id not in (self.bot.owner_id, self._author_id):  # type: ignore
                return False

        return payload.emoji in self.buttons

    @menus.button("\N{WHITE HEAVY CHECK MARK}")
    async def do_yes(self, _):
        self.response = True
        self.stop()

    @menus.button("\N{CROSS MARK}")
    async def do_no(self, _):
        self.response = False
        self.stop()

    async def get_response(self, ctx: commands.Context):
        await self.start(ctx, wait=True)
        return self.response


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

    @menus.button(
        "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f",
        skip_if=skip_one_or_two,
    )
    async def go_to_first_page(self, payload):
        """go to the first page"""
        await self.show_page(0)

    @menus.button("\N{BLACK LEFT-POINTING TRIANGLE}\ufe0f", skip_if=skip_only_one_page)
    async def go_to_previous_page(self, payload):
        """go to the previous page"""
        await self.show_checked_page(self.current_page - 1)

    @menus.button("\N{BLACK RIGHT-POINTING TRIANGLE}\ufe0f", skip_if=skip_only_one_page)
    async def go_to_next_page(self, payload):
        """go to the next page"""
        await self.show_checked_page(self.current_page + 1)

    @menus.button(
        "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f",
        skip_if=skip_one_or_two,
    )
    async def go_to_last_page(self, payload):
        """go to the last page"""
        # The call here is safe because it's guarded by skip_if
        await self.show_page(self._source.get_max_pages() - 1)  # type: ignore

    @menus.button("\N{BLACK SQUARE FOR STOP}\ufe0f", skip_if=skip_only_one_page)
    async def stop_pages(self, payload):
        """stops the pagination session."""
        await self.message.delete()  # type: ignore
        self.stop()


class NormalPageSource(menus.ListPageSource):
    def __init__(self, entries: Sequence[str], *, per_page: int = 1):
        super().__init__(entries, per_page=per_page)

    async def format_page(self, menu, page):
        if isinstance(page, str):
            return page
        else:
            return "\n".join(page)


class CodeblockPageSource(menus.ListPageSource):
    def __init__(
        self,
        entries: Sequence[str],
        *,
        per_page: int = 1,
        language: str | None = None,
    ):
        super().__init__(entries, per_page=per_page)
        self.language = language or ""

    async def format_page(self, menu, page):
        base = "```" + self.language + "\n"

        base += "\n".join(page)

        base += "\n```"

        return base


class EmbedFieldsPageSource(menus.ListPageSource):
    def __init__(
        self,
        entries: Sequence[EmbedFieldProxy],
        *,
        per_page: int = 1,
        title: str | None = None,
        description: str | None = None,
    ):
        super().__init__(entries, per_page=per_page)
        self.title = title
        self.description = description

    async def format_page(self, menu, page):
        base = discord.Embed(title=self.title, description=self.description)

        if isinstance(page, EmbedFieldProxy):
            return base.add_field(name=page.name, value=page.value, inline=page.inline)

        else:
            for proxy in page:
                base.add_field(name=proxy.name, value=proxy.value, inline=proxy.inline)
            return base


class FixedNonePaginator(commands.Paginator):
    @property
    def _max_size_factor(self):
        if self.prefix is not None and self.suffix is not None:
            return 2
        elif self.prefix is not None or self.suffix is not None:
            return 1
        else:
            return 0

    def add_line(self, line="", *, empty=False):
        max_page_size = (
            self.max_size - self._prefix_len - self._suffix_len - self._max_size_factor
        )
        if len(line) > max_page_size:
            raise RuntimeError("Line exceeds maximum page size %s" % max_page_size)

        if (
            self._count + len(line) + (0 if self.suffix is None else 1)
            > self.max_size - self._suffix_len
        ):
            self.close_page()

        self._count += len(line) + 1
        self._current_page.append(line)

        if empty:
            self._current_page.append("")
            self._count += 1


# Modified from https://github.com/Gorialis/jishaku/blob/master/jishaku/paginators.py#L322
# This isn't a subclass to deal with jishaku.flags
# This licence covers the class below
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
class PartitionPaginator(FixedNonePaginator):
    """
    Version of WrappedPaginator that uses str.rpartition
    """

    def __init__(self, *args, wrap_on=("\n", " "), include_wrapped=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.wrap_on = wrap_on
        self.include_wrapped = include_wrapped

    def add_line(self, line="", *, empty=False):
        true_max_size = (
            self.max_size - self._prefix_len - self._suffix_len - self._max_size_factor
        )

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

                    break

            if not wrapped:
                super().add_line(search_string, empty=empty)

        if len(line) > 0:
            super().add_line(line, empty=empty)


# TODO: replace this with a group-by subclass
class PrologPaginator(FixedNonePaginator):
    def __init__(
        self,
        prefix: str = "```prolog",
        suffix: str = "```",
        max_size: int = 500,
        align_option: str = ">",
        align_places: int = 16,
    ):
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
        header = f" {header} ".center(self.align_places * 2, "=")
        self.add_line(f"\n{capwords(str(header))}\n")

    def add_key_value_pair(self, key: str, value: str):
        """
        :param key: The key to add
        :param value: The value to add
        """
        self.add_line(
            f"{capwords(key):{self.align_option}{self.align_places}.{self.align_places}} :: "
            f"{capwords(value)}"
        )
