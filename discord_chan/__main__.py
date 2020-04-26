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
import sys
from pathlib import Path
from string import Template

import click
from aiomonitor import start_monitor, cli
from loguru import logger

import discord_chan
from discord_chan.utils import InterceptHandler, CaseSensitiveConfigParser

try:
    import uvloop
    uvloop.install()
except ImportError:
    uvloop = None

ROOT_DIR = Path(__file__).parent


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
@click.option('--no-cache', is_flag=True, help='Run without member cache')
def run(config, debug, no_cache):
    # noinspection PyArgumentList
    logging.basicConfig(handlers=[InterceptHandler()], level=0)

    logger.remove()
    logger.enable('discord_chan')
    logger.add(sys.stderr, level='INFO', filter='discord_chan')
    logger.add(sys.stderr, level='ERROR', filter='discord')

    # didn't feel like renaming
    config_file = config
    config = CaseSensitiveConfigParser(allow_no_value=True, strict=False)
    config.read(config_file)

    if not config['enviroment'].getboolean('disable'):
        load_environ(**dict([var for var in config['enviroment'].items() if var[0] != 'disable']))

    if debug:
        asyncio.get_event_loop().set_debug(True)
        logging.getLogger('asyncio').setLevel(logging.DEBUG)

    kwargs = {}
    if no_cache:
        kwargs['guild_subscriptions'] = False
        kwargs['fetch_offline_members'] = False

    bot = discord_chan.DiscordChan(config, **kwargs)

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
        environ[var] = value
        logger.debug(f'Set ENV var {var.upper()} = {value}')


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
            with open(ROOT_DIR / 'data' / 'default_config.txt') as fp:
                default_config = fp.read()

            config_file.write_text(default_config.strip())

        else:
            res = interactive_install()
            config_file.write_text(res)

        click.echo('Config file made/overwriten.')

    with open(ROOT_DIR / 'data' / 'default.sql') as fp:
        sql_init = fp.read()

    async def init_db():
        async with discord_chan.db.get_database() as connection:
            async with connection.cursor() as cursor:
                await cursor.executescript(sql_init.strip())
            await connection.commit()

        print('Initalized DB.')

    asyncio.run(init_db())

def interactive_install() -> str:
    with open(ROOT_DIR / 'data' / 'interactive_config.txt') as fp:
        interactive_config = Template(fp.read())

    click.echo('Starting interactive config...')
    click.echo('--general section--')

    prefix = click.prompt('Command prefix?')
    load_extensions = click.prompt('Load base extensions?', type=bool)

    click.echo('--discord section--')

    token = click.prompt('Discord bot token?')

    click.echo('--enviroment section--')

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
    # Todo: test
    main()
