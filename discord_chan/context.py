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

from discord import Message, HTTPException, NotFound
from discord.ext.commands import Context

from .menus import PartitionPaginator, NormalPageSource, DCMenuPages, ConfirmationMenu


class SubContext(Context):

    async def send(self, content=None, **kwargs) -> Message:
        """
        The paginator should never be used there as a just in case
        Also escapes_mentions, can be turned off by passing
        escape_mentions=False
        no_edit can be passed to not edit past invokes.
        """
        if content:
            content = str(content)

        menu = None

        # If there was more than just content ex: embeds they don't get sent
        # but this should never really be used, so this is ok?
        if content and len(str(content)) > 2000:
            paginator = PartitionPaginator(prefix=None, suffix=None, max_size=1985)
            paginator.add_line(content)

            source = NormalPageSource(paginator.pages)

            menu = DCMenuPages(source)

        if not kwargs.pop('no_edit', False) and self.message.id in self.bot.past_invokes:
            prev_msg = self.bot.past_invokes[self.message.id]

            if menu:
                menu.message = prev_msg
                await prev_msg.edit(embed=None)
                await menu.start(self, wait=True)
                return menu.message

            else:
                try:
                    await prev_msg.edit(
                        content=content,
                        embed=kwargs.pop('embed', None),
                        suppress=kwargs.pop('suppress', None),
                        delete_after=kwargs.pop('delete_after', None)
                    )
                    return prev_msg

                except NotFound:
                    pass

        if menu:
            await menu.start(self, wait=True)
            return menu.message

        new_msg = await super().send(
            content=content,
            **kwargs
        )

        self.bot.past_invokes[self.message.id] = new_msg
        return new_msg

    @property
    def created_at(self) -> datetime:
        """
        :return: When ctx.message was created
        """
        return self.message.created_at

    async def confirm(self, message: str = None) -> Optional[Message]:
        """
        Adds a checkmark to ctx.message.
        If unable to sends <message>
        """
        try:
            await self.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
        except HTTPException:
            message = message or '\N{WHITE HEAVY CHECK MARK}'
            return await self.send(message)

    async def prompt(self, message: str = None, *, owner_id: int = None, **send_kwargs) -> bool:
        """
        Prompt for <message> and return True or False
        """
        menu = ConfirmationMenu(message, owner_id=owner_id, send_kwargs=send_kwargs)
        return await menu.get_response(self)
