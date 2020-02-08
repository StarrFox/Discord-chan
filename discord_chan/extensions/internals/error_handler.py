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


# Todo: add the image errors if I do them (should be above commands.UserInputError)
async def on_command_error(ctx: commands.Context, error):
    error = getattr(error, 'original', error)

    str_send = (
        commands.CommandOnCooldown,
        commands.UserInputError,
        commands.MaxConcurrencyReached,
        commands.DisabledCommand,
        commands.CheckFailure
    )

    if isinstance(error, commands.CommandNotFound):
        return

    elif isinstance(error, str_send):
        return await ctx.send(str(error))

    elif isinstance(error, commands.MissingPermissions):
        return await ctx.send(
            f"You're missing the {', '.join(error.missing_perms)} permission(s) needed to run this command."
        )

    elif isinstance(error, commands.BotMissingPermissions):
        return await ctx.send(
            f"I'm missing the {', '.join(error.missing_perms)} permission(s) needed to run this command."
        )

    logger.error(
        f"Unhandled error in command {ctx.command.name}\n"
        f"Invoke message: {ctx.message.content}",
        exc_info=(type(error), error, error.__traceback__)
    )


def setup(bot: commands.Bot):
    bot.add_listener(on_command_error)


def teardown(bot: commands.Bot):
    bot.remove_listener(on_command_error)
