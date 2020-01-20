# -*- coding: utf-8 -*-
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

import argparse
import asyncio
import logging
from configparser import ConfigParser

from aiomonitor import start_monitor

import discord_chan

default_config = """
[general]
prefix=dc!
support_invite=
source_url=
# true of false of if default extensions (discord_chan/extensions)
# should be loaded
load_extensions=true

[discord]
# Discord Bot token
token=

[enviroment]
# all options here will be loaded as enviroment variables
# unless the disable option is true
# note: all keys are uppered to deal with configParser
disable=false

# read more about these jishaku setting in the README
JISHAKU_HIDE=true
JISHAKU_NO_DM_TRACEBACK=true
JISHAKU_NO_UNDERSCORE=true
JISHAKU_RETAIN=true
"""

sql_init = """
CREATE TABLE IF NOT EXISTS prefixes (
    guild_id INTEGER PRIMARY KEY,
    prefixes PYSET
);

CREATE TABLE IF NOT EXISTS command_uses (
    name TEXT PRIMARY KEY,
    uses INTEGER
);

CREATE TABLE IF NOT EXISTS socket_stats (
    name TEXT PRIMARY KEY,
    amount INTEGER
);
"""

def run(args: argparse.Namespace):
    config = ConfigParser(allow_no_value=True, strict=False)
    config.read(args.config)

    if not config['enviroment'].getboolean('disable'):
        load_environ(**dict([var for var in config['enviroment'].items() if var[0] != 'disable']))

    logging.basicConfig(
        format="[%(asctime)s] [%(levelname)s:%(name)s] %(message)s",
        level=logging.DEBUG if args.debug else logging.INFO
    )

    if args.debug:
        asyncio.get_event_loop().set_debug(True)
        logging.getLogger('asyncio').setLevel(logging.DEBUG)

    dc_log = logging.getLogger('discord_chan')
    dpy_log = logging.getLogger('discord')

    if args.logfile:
        handler = logging.FileHandler(args.logfile)
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s:%(name)s] %(message)s")
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG if args.debug else logging.INFO)

        dc_log.addHandler(handler)
        dpy_log.addHandler(handler)

        dc_log.propagate = False
        dpy_log.propagate = False

    bot = discord_chan.DiscordChan(config)

    if args.load_jsk:
        bot.load_extension('jishaku')

    # # Todo: make sure to remove this debug call
    # bot.dispatch('ready')

    loop = asyncio.get_event_loop()
    with start_monitor(loop, monitor=discord_chan.DiscordChanMonitor, locals={'bot': bot}):
        bot.run()

def load_environ(**kwargs):
    """
    Loads the kwargs as enviroment variables
    :param kwargs: The enviroment variables to load
    :return:
    """

    from os import environ

    for var, value in kwargs.items():
        environ[var.upper()] = value

def add_run_args(parser: argparse.ArgumentParser):
    parser.add_argument('-v',
                        '--version',
                        action='version',
                        version=discord_chan.__version__
                        )

    parser.add_argument('-d',
                        '--debug',
                        action='store_true',
                        help='Run in debug mode.'
                        )

    parser.add_argument('-c',
                        '--config',
                        action='store',
                        default='config.ini',
                        help='Path to config file, defaults to config.ini.'
                        )

    parser.add_argument('-lf',
                        '--logfile',
                        action='store',
                        default=None,
                        help='Path to logging file, defaults to stdout.'
                        )

    parser.add_argument('-lj',
                        '--load-jsk',
                        action='store_true',
                        default=True,
                        help='If the Jishaku debug cog should be loaded, defaults to true')

    parser.set_defaults(func=run)


def install(args: argparse.Namespace):
    # todo: Use pathlib and touch here and prompt to reset if already exists
    with open(args.config, 'w+') as file:
        file.write(default_config.strip())
        print(f'{args.config} made.')

    async def init_db():
        async with discord_chan.db.get_database() as connection:
            async with connection.cursor() as cursor:
                await cursor.executescript(sql_init.strip())
                # Todo: remove before pushing master
                # await cursor.execute('INSERT INTO prefixes VALUES (?, ?)', (1234, {'a', 'b'}))
            await connection.commit()

        print('Initalized DB.')

    asyncio.run(init_db())

def add_install_args(parser: argparse.ArgumentParser):
    parser.add_argument('-c',
                        '--config',
                        action='store',
                        default='config.ini',
                        help='Path to config file, defaults to config.ini.'
                        )

    parser.set_defaults(func=install)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog='discord_chan', description='General purpose Discord bot.')

    add_run_args(parser)

    subcommands = parser.add_subparsers()
    install_command = subcommands.add_parser('install', help='\"Install\" the bot; make config file and setup DB.')

    add_install_args(install_command)

    return parser.parse_args()


def main():
    args = parse_args()

    args.func(args)


if __name__ == '__main__':
    main()
