from datetime import datetime
from typing import TYPE_CHECKING

from discord import HTTPException, Message
from typing_extensions import override
from loguru import logger

from .menus import ConfirmationMenu, DCMenuPages, NormalPageSource, PartitionPaginator
from .typing_helpers import GuildContext

if TYPE_CHECKING:
    from discord_chan import DiscordChan


# we disallow dm commands globally so we should never be in a dm context
class SubContext(GuildContext["DiscordChan"]):
    @override
    async def send(self, content: str | None = None, **kwargs) -> Message:
        if content and len(content) > 2000:
            logger.debug("entered ctx.send auto-paginate")

            if kwargs:
                raise RuntimeError(
                    "content over 2000 but kwargs were provided and wont be respected"
                )

            paginator = PartitionPaginator(prefix=None, suffix=None, max_size=1985)
            paginator.add_line(content)

            source = NormalPageSource(paginator.pages)

            menu = DCMenuPages(source)

            await menu.start(self, wait=True)
            assert menu.message is not None
            return menu.message

        # TODO: better handle when target message was deleted i.e. purge
        # replies
        kwargs["reference"] = kwargs.get("reference", self.message)
        kwargs["mention_author"] = kwargs.get("mention_author", False)

        return await super().send(content=content, **kwargs)

    @property
    def created_at(self) -> datetime:
        """
        :return: When ctx.message was created
        """
        return self.message.created_at

    async def confirm(self, message: str | None = None) -> Message | None:
        """
        Adds a checkmark to ctx.message.
        If unable to sends <message>
        """
        try:
            await self.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
        except HTTPException:
            message = message or "\N{WHITE HEAVY CHECK MARK}"
            return await self.send(message)

    async def deny(self, message: str | None = None) -> Message | None:
        """
        Adds a cross to ctx.message.
        If unable to sends <message>
        """
        try:
            await self.message.add_reaction("\N{CROSS MARK}")
        except HTTPException:
            message = message or "\N{CROSS MARK}"
            return await self.send(message)

    async def prompt(
        self, message: str | None = None, *, owner_id: int | None = None, **send_kwargs
    ) -> bool:
        """
        Prompt for <message> and return True or False
        """
        message = message or "confirm?"
        owner_id = owner_id or self.author.id
        menu = ConfirmationMenu(message, owner_id=owner_id, send_kwargs=send_kwargs)
        return await menu.get_response(self)
