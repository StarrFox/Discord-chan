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

import logging
from logging import NullHandler
from pathlib import Path

from . import utils, db, checks
from .bot import DiscordChan
from .monitor import DiscordChanMonitor
from .converters import *
from .games import *
from .help import *
from .image import *
from .menus import *
from .snipe import *
from .context import SubContext


__version__ = '1.4.0'

logging.getLogger(__name__).addHandler(NullHandler())
ROOT = Path(__file__).parent
