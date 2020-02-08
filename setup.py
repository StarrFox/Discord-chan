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

import re

from setuptools import setup

with open('discord_chan/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

setup(
    name='discord_chan',
    description='General purpose Discord bot.',
    license='GNU Affero General Public License',
    author='StarrFox',
    version=version,
    packages=['discord_chan', 'discord_chan.extensions.commands', 'discord_chan.extensions.internals'],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'discord_chan = discord_chan.__main__:main'
        ]
    },
    python_requires='>=3.7',
    install_requires=[
        'jishaku>=1.17',
        'discord.py>=1.3',
        'numpy',
        'imagehash',
        'aiohttp',
        'humanize',
        'Pillow>=6.2.1',
        'colorclass==2.2.0',
        'terminaltables==3.1.0',
        'aiomonitor==0.4.5',
        'jikanpy',
        'aiosqlite',
        'discord-flags',
        'git+https://github.com/Rapptz/discord-ext-menus'  # Todo: remove when released
    ]
)
