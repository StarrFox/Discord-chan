from datetime import timedelta

import humanize
from discord.ext import commands
from loguru import logger


async def on_command_error(ctx: commands.Context, error: Exception):
    error = getattr(error, "original", error)

    if isinstance(error, commands.CommandNotFound):
        return

    # Bypass checks for owner
    elif isinstance(error, commands.CheckFailure) and await ctx.bot.is_owner(
        ctx.author
    ):
        await ctx.reinvoke()
        return

    # Reset cooldown when command doesn't finish
    elif isinstance(error, commands.CommandError) and not isinstance(
        error, commands.CommandOnCooldown
    ):
        ctx.command.reset_cooldown(ctx)
        return await ctx.send(str(error))

    elif isinstance(error, commands.CommandOnCooldown):
        delta = timedelta(seconds=error.retry_after)
        natural = humanize.naturaldelta(delta)
        return await ctx.send(f"Command on cooldown, retry in {natural}.")

    # TODO: find out why this doesn't work
    logger.opt(exception=(type(error), error, error.__traceback__)).error(
        f"Unhandled error in command {ctx.command.name}\nInvoke message: {ctx.message.content}"
    )

    await ctx.send(f"Unknown error while executing {ctx.command}: {error}")


async def setup(bot: commands.Bot):
    bot.add_listener(on_command_error)


async def teardown(bot: commands.Bot):
    bot.remove_listener(on_command_error)
