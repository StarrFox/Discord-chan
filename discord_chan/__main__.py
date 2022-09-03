import asyncio
import logging
import sys
import os
from pathlib import Path

import click
import dotenv
from click_default_group import DefaultGroup
from loguru import logger

import discord_chan
from discord_chan.utils import InterceptHandler

try:
    import uvloop
except ImportError:
    uvloop = None
else:
    uvloop.install()

dotenv.load_dotenv()

ROOT_DIR = Path(__file__).parent


@click.group(
    help="General purpose Discord bot.",
    cls=DefaultGroup,
    default="run",
    default_if_no_args=True,
)
def main():
    pass


@main.command(help="Run the bot")
@click.option("--debug", is_flag=True, help="Run in debug mode.")
def run(debug):
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
    bot.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    main()
