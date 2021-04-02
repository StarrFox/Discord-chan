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

DEFAULT_SQL = """
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
CREATE TABLE IF NOT EXISTS blacklist (
    user_id INTEGER PRIMARY KEY,
    reason TEXT
);
CREATE TABLE IF NOT EXISTS grubninja_settings (
    key TEXT PRIMARY KEY,
    "value" TEXT
);
""".strip()


DEFAULT_CONFIG = """
[general]
prefix=dc/
support_url=
source_url=https://github.com/StarrFox/Discord-chan
vote_url=
# true or false on if default extensions (discord_chan/extensions)
# should be loaded
load_extensions=true

[discord]
# Discord Bot token
token=
# needs manage_webhooks to log
logging_channel=

[extra_tokens]
emote_collector=
top_gg=
api_token=
product_id=

[enviroment]
# all options here will be loaded as environment variables
# unless the disable option is true
disable=false

# read more about these jishaku setting in the README
JISHAKU_HIDE=true
JISHAKU_NO_DM_TRACEBACK=true
JISHAKU_NO_UNDERSCORE=true
JISHAKU_RETAIN=true
""".strip()


INTERACTIVE_CONFIG = """
[general]
prefix=$prefix
support_url=
source_url=https://github.com/StarrFox/Discord-chan
vote_url=
# true or false on if default extensions (discord_chan/extensions)
# should be loaded
load_extensions=$load_extensions

[discord]
# Discord Bot token
token=$token
# needs manage_webhooks to log
logging_channel=

[extra_tokens]
emote_collector=
tog_gg=
api_token=
product_id=

[enviroment]
# all options here will be loaded as environment variables
# unless the disable option is true
disable=$disable

# read more about these jishaku setting in the README
JISHAKU_HIDE=true
JISHAKU_NO_DM_TRACEBACK=true
JISHAKU_NO_UNDERSCORE=true
JISHAKU_RETAIN=true
""".strip()
