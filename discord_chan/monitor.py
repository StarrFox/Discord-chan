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

from aiomonitor import Monitor
from aiomonitor.utils import alt_names
from terminaltables import AsciiTable

version_message = f"Discord Chan Monitor v1.0\n"

BOOL_DICT = {
    'true': True,
    '1': True,
    'false': False,
    '0': False
}

def convert_bool(arg):
    return BOOL_DICT[arg]


class DiscordChanMonitor(Monitor):
    intro = version_message + "{tasknum} task{s} running. Use help (?) for commands.\n"
    prompt = "Discord Chan >>>"

    def do_status(self):
        """Status overview of the bot."""
        from discord import __version__ as dpy_version
        from discord_chan import __version__ as dc_version

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

    @alt_names('disable')
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

        for command in sorted(bot.walk_commands(), key=lambda cmd: cmd.cog_name or ''):

            table_data.append([
                command.full_parent_name + ' ' + command.name,
                command.cog_name,
                command.enabled,
                command.hidden
            ])

        table = AsciiTable(table_data)
        self._sout.write(table.table + '\n')

    # Todo: add db quarry command
