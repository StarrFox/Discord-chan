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

import logging

from discord.ext import commands

logger = logging.getLogger(__name__)


async def on_command_error(ctx: commands.Context, error):
    error = getattr(error, 'original', error)

    if isinstance(error, commands.CommandNotFound):
        return

    elif isinstance(error, commands.CommandError) and not isinstance(error, commands.CommandOnCooldown):
        ctx.command.reset_cooldown(ctx)
        return await ctx.send(str(error))

    elif isinstance(error, commands.CommandOnCooldown):
        return await ctx.send(str(error))

    logger.error(
        f"Unhandled error in command {ctx.command.name}\n"
        f"Invoke message: {ctx.message.content}",
        exc_info=(type(error), error, error.__traceback__)
    )


def setup(bot: commands.Bot):
    bot.add_listener(on_command_error)


def teardown(bot: commands.Bot):
    bot.remove_listener(on_command_error)
