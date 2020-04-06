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

import asyncio
import logging
from configparser import ConfigParser
from pathlib import Path
from string import Template

import click
from aiomonitor import start_monitor, cli

import discord_chan

try:
    import uvloop
    uvloop.install()
except ImportError:
    uvloop = None


default_config = """
[general]
prefix=dc/
support_url=
source_url=https://github.com/StarrFox/Discord-chan
vote_url=
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

interactive_config = Template("""
[general]
prefix=$prefix
support_url=
source_url=https://github.com/StarrFox/Discord-chan
vote_url=
# true of false of if default extensions (discord_chan/extensions)
# should be loaded
load_extensions=$load_extensions

[discord]
# Discord Bot token
token=$token

[enviroment]
# all options here will be loaded as enviroment variables
# unless the disable option is true
# note: all keys are uppered to deal with configParser
disable=$disable

# read more about these jishaku setting in the README
JISHAKU_HIDE=true
JISHAKU_NO_DM_TRACEBACK=true
JISHAKU_NO_UNDERSCORE=true
JISHAKU_RETAIN=true
""")

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

CREATE TABLE IF NOT EXISTS channel_links (
    send_from INTEGER PRIMARY KEY,
    send_to PYSET
);

CREATE TABLE IF NOT EXISTS ratings (
    bot_id INTEGER,
    user_id INTEGER,
    rating INTEGER,
    review TEXT,
    PRIMARY KEY(bot_id, user_id)
);
"""


# Todo: add update subparser? git pull, see if config or sql is different?
# Todo: add gui subparser? shows stats and has buttons to start/stop bot
@click.group(help='General purpose Discord bot.')
def main():
    pass

@main.command(help='Run the bot')
@click.option('--config',
              default='config.ini',
              type=click.Path(exists=True),
              show_default=True,
              help='Path to config file.')
@click.option('--debug', is_flag=True, help='Run in debug mode.')
def run(config, debug):
    # didn't feel like renaming
    config_file = config
    config = ConfigParser(allow_no_value=True, strict=False)
    config.read(config_file)

    if not config['enviroment'].getboolean('disable'):
        load_environ(**dict([var for var in config['enviroment'].items() if var[0] != 'disable']))

    logging.basicConfig(
        format="[%(asctime)s] [%(levelname)s:%(name)s] %(message)s",
        level=logging.DEBUG if debug else logging.INFO
    )

    if debug:
        asyncio.get_event_loop().set_debug(True)
        logging.getLogger('asyncio').setLevel(logging.DEBUG)

    dpy_log = logging.getLogger('discord')

    dpy_log.setLevel(logging.DEBUG if debug else logging.WARNING)

    bot = discord_chan.DiscordChan(config)

    # Todo: make sure to remove this debug call
    # bot.dispatch('ready')

    loop = asyncio.get_event_loop()
    with start_monitor(loop,
                       monitor=discord_chan.DiscordChanMonitor,
                       locals={'bot': bot}):
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


@main.command(help='\"Install\" the bot; general setup before running.')
@click.option('--config',
              default='config.ini',
              type=click.Path(),
              show_default=True,
              help='Path to config file.'
              )
@click.option('--interactive', is_flag=True, help='Interactive config file setup.')
def install(config, interactive):
    config_file = Path(config)

    if config_file.exists():
        overwrite = click.confirm('Config file already exists, overwrite?')

    else:
        overwrite = True

        try:
            config_file.touch()

        except Exception as e:
            exit(str(e))

    if overwrite:
        if not interactive:
            config_file.write_text(default_config.strip())

        else:
            res = interactive_install()
            config_file.write_text(res)

        click.echo('Config file made/overwriten.')

    async def init_db():
        async with discord_chan.db.get_database() as connection:
            async with connection.cursor() as cursor:
                await cursor.executescript(sql_init.strip())
            await connection.commit()

        print('Initalized DB.')

    asyncio.run(init_db())

def interactive_install() -> str:
    click.echo('Starting interactive config...')
    click.echo('--general section--')

    prefix = click.prompt('Command prefix?')
    load_extensions = click.prompt('Load base extensions?', type=bool)

    click.echo('--discord section--')

    token = click.prompt('Discord bot token?')

    click.echo('enviroment section:')

    disable = click.prompt('Disable enviroment var config?', type=bool)

    return interactive_config.substitute(
        prefix=prefix,
        load_extensions=load_extensions,
        token=token,
        disable=disable
    )


@main.command(help='Start the DiscordChanMonitor interface.')
@click.option('-H', '--host', default='127.0.0.1', type=str, help='Monitor host ip.')
@click.option('-P', '--port', default=50101, type=int, help='Monitor port number.')
def monitor(host, port):
    cli.monitor_client(host, port)


if __name__ == '__main__':
    main()
