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
from datetime import datetime

import aiohttp
import bot_stuff
import discord
from bot_stuff import DiscordHandler
from discord.ext import commands, tasks

import config

try:
    import asyncpg
except ImportError:
    asyncpg = False

logger = logging.getLogger(__name__)
logger.propagate = False

if not logger.handlers:
    logger.addHandler(
        DiscordHandler(
            config.webhook_url,
            logging.INFO
        )
    )

jsk_settings = {
    "task": "<a:sonic:577005444191485952>",
    "done": "<a:dancin:582409853918511165>",
    "syntax": "<a:default:577017740016222229>",
    "timeout": "error:539157627385413633",
    "error": "<a:default:577017740016222229>",
    "tracebacks": "\N{BLACK DOWN-POINTING DOUBLE TRIANGLE}",
    "scope_prefix": "",
    "retain": True,
    "channel_tracebacks": True
}


class DiscordChan(bot_stuff.Bot):

    def __init__(self):
        super().__init__(
            prefix=self.get_prefix,
            owners=[285148358815776768],
            extension_dir="cogs",
            case_insensitive=True,
            reconnect=True
        )
        self.db = None
        self.prefixes = {}
        self.uptime = datetime.now()
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.presence_cycle.start()  # pylint: disable=no-member
        self.noprefix = False

    @tasks.loop(hours=1)
    async def presence_cycle(self):
        """
        Keeps the status message active
        """
        prez = f"{len(self.guilds)} Guilds | {config.prefix}help"
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=prez))

    @presence_cycle.before_loop
    async def presence_cycle_before(self):
        await self.wait_until_ready()

    async def get_prefix(self, message: discord.Message):
        if not message.guild:
            return [config.prefix, ""]
        if self.noprefix and await self.is_owner(message.author):
            return ""
        elif message.guild.id in self.prefixes:
            return commands.when_mentioned_or(*self.prefixes[message.guild.id])(self, message)
        else:
            return commands.when_mentioned_or(config.prefix)(self, message)

    async def connect_db(self):
        self.db = await asyncpg.connect(
            config.db_link,
            password=config.db_pass
        )
        logger.info("Connected to DB.")

    async def load_prefixes(self):
        for guild_id, prefix_list in await self.db.fetch("SELECT * FROM prefixes;"):
            self.prefixes[guild_id] = prefix_list
        logger.info(f"Loaded {len(self.prefixes)} prefixes.")

    async def unload_prefixes(self):
        await self.db.execute("DELETE FROM prefixes;")
        await self.db.executemany("INSERT INTO prefixes(guild_id, prefixes) VALUES ($1, $2)", self.prefixes.items())
        logger.info(f"Unloaded {len(self.prefixes)} prefixes.")


bot = DiscordChan()

bot.help_command = bot_stuff.Minimal()

bot.load_extension("bot_stuff.jsk", **jsk_settings)

bot.load_extension("bot_stuff.logging_cog", webhook_url=config.webhook_url)

if config.load_db and asyncpg:
    bot.add_ready_func(bot.connect_db)
    bot.add_ready_func(bot.load_prefixes)

    bot.add_logout_func(bot.unload_prefixes)

bot.run(config.token)
