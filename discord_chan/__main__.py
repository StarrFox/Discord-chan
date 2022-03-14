#  Copyright © 2019 StarrFox
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
@click.option("--no-cache", is_flag=True, help="Run without member cache")
def run(debug, no_cache):
    # noinspection PyArgumentList
    logging.basicConfig(handlers=[InterceptHandler()], level=0)

    logger.remove()
    logger.enable("discord_chan")
    logger.add(sys.stderr, level="INFO", filter="discord_chan")
    logger.add(sys.stderr, level="ERROR", filter="discord")

    if debug:
        asyncio.get_event_loop().set_debug(True)
        logging.getLogger("asyncio").setLevel(logging.DEBUG)

    kwargs = {}
    if no_cache:
        kwargs["guild_subscriptions"] = False
        kwargs["fetch_offline_members"] = False

    bot = discord_chan.DiscordChan(**kwargs)

    # Todo: make sure to remove this debug call
    # bot.dispatch("ready")

    bot.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    # Todo: test
    main()
