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
from typing import Optional

from discord import Message, utils, HTTPException
from discord.ext.commands import Context

from .paginators import PartitionPaginator, NormalPageSource, DCMenuPages


class SubContext(Context):

    async def send(self, content=None, **kwargs) -> Message:
        """
        The paginator should never be used there as a just in case
        Also escapes_mentions, can be turned off by passing
        escape_mentions=False
        """
        if kwargs.pop('escape_mentions', True) and content:
            content = utils.escape_mentions(content)

        # If there was more than just content ex: embeds they don't get sent
        # but this should never really be used, so this is ok?
        if content and len(str(content)) > 2000:

            paginator = PartitionPaginator(prefix=None, suffix=None, max_size=1985)
            paginator.add_line(content)

            source = NormalPageSource(paginator.pages)

            menu = DCMenuPages(source)

            await menu.start(self, wait=True)
            return menu.message

        else:

            return await super().send(
                content=content,
                **kwargs
            )

    @property
    def created_at(self) -> datetime:
        """
        :return: When ctx.message was created
        """
        return self.message.created_at

    async def confirm(self, message: str = None) -> Optional[Message]:
        """Adds a checkmark to ctx.message"""
        try:
            await self.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
        except HTTPException:
            message = message or '\N{WHITE HEAVY CHECK MARK}'
            return await self.send(message)

    # Todo: prompt
