import asyncio

import pendulum
from discord.ext import commands
from loguru import logger

from discord_chan.utils import to_discord_timestamp


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
        if ctx.command is not None:
            ctx.command.reset_cooldown(ctx)

        return await ctx.send(str(error))

    elif isinstance(error, commands.CommandOnCooldown):
        now = pendulum.now()
        cooldown_over = now.add(seconds=int(error.retry_after))

        cooldown_message = await ctx.reply(
            f"Command on cooldown, retry in {to_discord_timestamp(cooldown_over)}",
            mention_author=False,
        )

        await asyncio.sleep(error.retry_after)
        await cooldown_message.edit(content="Cooldown over")

        return

    # TODO: find out why this doesn't work
    logger.opt(exception=(type(error), error, error.__traceback__)).error(
        f"Unhandled error in command {ctx.command} Invoke message: {ctx.message.content}"
    )

    await ctx.send(f"Unknown error while executing {ctx.command}: {error}")


async def setup(bot: commands.Bot):
    bot.add_listener(on_command_error)


async def teardown(bot: commands.Bot):
    bot.remove_listener(on_command_error)
