import asyncio
import logging
import os
import sys
from pathlib import Path

import click
from loguru import logger

import discord_chan
from discord_chan.utils import InterceptHandler

# only works on linux
try:
    import uvloop
except ImportError:
    uvloop = None
else:
    uvloop.install()


os.environ["JISHAKU_HIDE"] = "true"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "true"
os.environ["JISHAKU_NO_UNDERSCORE"] = "true"
os.environ["JISHAKU_RETAIN"] = "true"

ROOT_DIR = Path(__file__).parent


@click.command()
@click.option("--debug", is_flag=True, help="Run in debug mode.")
@click.option(
    "--secret",
    help="Path to secret file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default="discord_token.secret",
)
def main(debug: bool, secret: Path):
    # noinspection PyArgumentList
    logging.basicConfig(handlers=[InterceptHandler()], level=0)

    logger.remove()
    logger.enable("discord_chan")
    logger.add(sys.stderr, level="INFO", filter="discord_chan")
    logger.add(sys.stderr, level="ERROR", filter="discord")

    if debug:
        asyncio.get_event_loop().set_debug(True)
        logging.getLogger("asyncio").setLevel(logging.DEBUG)

    bot = discord_chan.DiscordChan()

    with open(secret) as fp:
        discord_token = fp.read().strip("\n")

    bot.run(discord_token)


if __name__ == "__main__":
    main()
