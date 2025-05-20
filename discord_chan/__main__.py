import asyncio
import logging
import os
import sys
from pathlib import Path

import click
from loguru import logger
from loguru_logging_intercept import setup_loguru_logging_intercept

import discord_chan

# only works on linux
try:
    import uvloop  # type: ignore
except ImportError:
    uvloop = None
else:
    uvloop.install()


os.environ["JISHAKU_HIDE"] = "true"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "true"
os.environ["JISHAKU_NO_UNDERSCORE"] = "true"
os.environ["JISHAKU_RETAIN"] = "true"


@click.command()
@click.option("--debug", is_flag=True, help="Run in debug mode")
@click.option(
    "--secret",
    help="Path to secret file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default="discord_token.secret",
)
@click.option(
    "--exaroton",
    help="Path to exaroton token",
    type=click.Path(dir_okay=False, path_type=Path),
    default="exaroton.secret"
)
@click.option(
    "--datastore",
    help="Path to datastore root",
    type=click.Path(dir_okay=True, file_okay=False, path_type=Path, resolve_path=True),
    default="store"
)
def main(debug: bool, secret: Path, exaroton: Path, datastore: Path):
    setup_loguru_logging_intercept(
        level=logging.DEBUG,
        modules=("discord"),
    )

    # the logging module is so garbage
    logging.getLogger("discord.client").setLevel(logging.WARNING)
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)

    logger.remove()
    logger.enable("discord_chan")
    logger.add(sys.stderr, level="INFO", filter="discord_chan")

    if debug:
        asyncio.get_event_loop().set_debug(True)
        logging.getLogger("asyncio").setLevel(logging.DEBUG)

    if exaroton.exists():
        with open(exaroton) as fp:
            exaroton_token = fp.read().strip("\n")
    else:
        exaroton_token = None

    bot = discord_chan.DiscordChan(debug_mode=debug, exaroton_token=exaroton_token, datastore_root=datastore)

    with open(secret) as fp:
        discord_token = fp.read().strip("\n")

    bot.run(discord_token)


if __name__ == "__main__":
    main()
