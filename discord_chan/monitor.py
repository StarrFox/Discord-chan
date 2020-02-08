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

import asyncio

from aiomonitor import Monitor
from aiomonitor.utils import alt_names
from terminaltables import AsciiTable

from . import db

version_message = f"Discord Chan Monitor v1.1\n"

BOOL_DICT = {
    'true': True,
    '1': True,
    'false': False,
    '0': False
}


def convert_bool(arg):
    return BOOL_DICT[arg.lower()]


# noinspection PyUnresolvedReferences,PyUnresolvedReferences
class DiscordChanMonitor(Monitor):
    intro = version_message + "{tasknum} task{s} running. Use help (?) for commands.\n"
    prompt = "Discord Chan >>>"

    def do_status(self):
        """Status overview of the bot."""
        from discord_chan import __version__ as dc_version
        from discord import __version__ as dpy_version

        bot = self._locals['bot']

        table_data = [
            ['Stat', 'Value'],
            ['Extensions', len(bot.extensions)],
            ['Commands', len(bot.commands)],
            ['Latency', f'{bot.latency * 1000}ms'],
            ['Discord Chan', f'v{dc_version}'],
            ['Discord.py', f'v{dpy_version}']
        ]

        table = AsciiTable(table_data, 'AutoSharded')
        self._sout.write(table.table + '\n')

    def do_extensions(self):
        """List current extensions."""
        bot = self._locals['bot']

        self._sout.write('\n'.join(bot.extensions) + '\n')

    def do_enable(self, mode: convert_bool, command: str):
        """Enable or disable a command."""
        bot = self._locals['bot']

        attempt = bot.get_command(command)
        if not attempt:
            self._sout.write(f'Command "{command}" not found.\n')
            return

        attempt.enabled = mode
        self._sout.write(f'Command "{command}".enabled set to {mode}.\n')

    @alt_names('cmds')
    def do_commands(self):
        """Current commands and their status."""
        bot = self._locals['bot']

        table_data = [
            ['Name', 'Cog', 'Enabled', 'Hidden']
        ]

        for command in sorted(set(bot.walk_commands()), key=lambda cmd: cmd.cog_name or ''):
            table_data.append([
                command.full_parent_name + ' ' + command.name,
                command.cog_name,
                command.enabled,
                command.hidden
            ])

        table = AsciiTable(table_data)
        self._sout.write(table.table + '\n')

    def do_db(self, *quarry: str):
        """Execute a db quarry."""

        async def execute_quarry():
            async with db.get_database() as connection:
                cursor = await connection.execute(' '.join(quarry))
                await connection.commit()
                quarry_result = await cursor.fetchall()
                if quarry_result:
                    collums = [coll[0] for coll in cursor.description]
                    final = [collums]
                    for data in quarry_result:
                        final.append(list(data))
                    return final

        future = asyncio.run_coroutine_threadsafe(execute_quarry(), self._loop)

        try:
            result = future.result(20)
        except asyncio.TimeoutError:
            self._sout.write('Timed out.\n')
            future.cancel()
        except Exception as exc:
            self._sout.write(str(exc) + '\n')
        else:
            if result:
                table = AsciiTable(result)
                self._sout.write(table.table + '\n')
            else:
                self._sout.write('No result.\n')
