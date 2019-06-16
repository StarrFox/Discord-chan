import discord
from discord.ext import commands, tasks

import asyncio
import json
import os
from datetime import datetime
import asyncpg
import aiohttp
import logging
import traceback
import io
import bot_stuff

from extras import utils

logging.basicConfig(
    format="[%(asctime)s] [%(levelname)s:%(name)s] %(message)s", level=logging.INFO
)

jsk_settings = {
    "task": "<a:sonic:577005444191485952>",
    "done": "<a:dancin:582409853918511165>",
    "syntax": "<a:default:577017740016222229>",
    "timeout": "error:539157627385413633",
    "error": "<a:default:577017740016222229>",
    "tracebacks": "\N{BLACK DOWN-POINTING DOUBLE TRIANGLE}",
    "scope_prefix": ""
}

class DiscordChan(bot_stuff.Bot):

    def __init__(self):
        super().__init__(
            command_prefix=self.get_prefix,
            case_insensitive=True,
            reconnect=True
        )
        self.first_run = True
        with open('settings.json') as tf:
            self.settings = json.load(tf)
            tf.close()
        self.logger = logging.getLogger(__name__)
        self.owners = [
            285148358815776768,
            455289384187592704
        ]
        self.db = None
        self.prefixes = {}
        self.uptime = datetime.now()
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.presence_cycle.start()
        self.noprefix = False
        self.extension_dir = "cogs"

    @tasks.loop(minutes=5)
    async def presence_cycle(self):
        toggle = True
        if toggle:
            prez = f"dc!help | {len(self.guilds)} servers"
            toggle = False
        else:
            prez = f"dc!help | {len(self.users)} users"
            toggle = True
        await self.change_presence(activity=discord.Game(prez))

    @presence_cycle.before_loop
    async def presence_cycle_befoe(self):
        await self.wait_until_ready()

    async def get_prefix(self, message):
        if not message.guild:
            return ""
        if self.noprefix and await self.is_owner(message.author):
            return ""
        elif message.guild.id in self.prefixes:
            return commands.when_mentioned_or(*self.prefixes[message.guild.id])(self, message)
        else:
            return "dc!"

    async def on_ready(self):
        if not self.first_run:
            return
        await self.connect_db()
        await self.load_prefixes()
        await self.load_mods()
        self.logger.info("Bot ready")
        self.first_run = False

    async def connect_db(self):
        self.db = await asyncpg.connect(
            self.settings['db'],
            password=self.settings['db_pass']
        )
        self.logger.info("Connected to DB")

    async def load_prefixes(self):
        count = 0
        for guild_id, prefix_list in await self.db.fetch("SELECT * FROM prefixes;"):
            count += 1
            self.prefixes[guild_id] = prefix_list
        self.logger.info(f"loaded {count} prefixes")

    async def unload_prefixes(self):
        await self.db.execute("DELETE FROM prefixes;")
        await self.db.executemany("INSERT INTO prefixes(guild_id, prefixes) VALUES ($1, $2)", self.prefixes.items())
        self.logger.info("Unloaded prefixes")

    def run(self):
        super().run(self.settings['token'])

    async def logout(self):
        if self.prefixes:
            await self.unload_prefixes()
        for extension in tuple(self.extensions):
            try:
                self.unload_extension(extension)
            except Exception:
                pass
        for cog in tuple(self.cogs):
            try:
                self.remove_cog(cog)
            except Exception:
                pass
        await asyncio.sleep(5)
        await self.db.close()
        await super().logout()

bot = DiscordChan("cogs")
bot.load_extension("bot_stuff.jsk", **jsk_settings)
bot.run()