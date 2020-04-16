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

from datetime import timedelta

from discord.ext import commands
from humanize import naturaldelta
from loguru import logger


async def on_command_error(ctx: commands.Context, error):
    error = getattr(error, 'original', error)

    if isinstance(error, commands.CommandNotFound):
        return

    # Bypass checks for owner
    elif isinstance(error, commands.CheckFailure) and await ctx.bot.is_owner(ctx.author):
        await ctx.reinvoke()
        return

    # Reset cooldown when command doesn't finish
    elif isinstance(error, commands.CommandError) and not isinstance(error, commands.CommandOnCooldown):
        ctx.command.reset_cooldown(ctx)
        return await ctx.send(str(error))

    elif isinstance(error, commands.CommandOnCooldown):
        delta = timedelta(seconds=error.retry_after)
        natural = naturaldelta(delta)
        return await ctx.send(f'Command on cooldown, retry in {natural}.')

    logger.opt(exception=(type(error), error, error.__traceback__)).error(
        f"Unhandled error in command {ctx.command.name}\nInvoke message: {ctx.message.content}"
    )

    await ctx.send(
        f'Unknown error while executing {ctx.command}, you can join the support server (`support` command) for updates'
    )


def setup(bot: commands.Bot):
    bot.add_listener(on_command_error)


def teardown(bot: commands.Bot):
    bot.remove_listener(on_command_error)
