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
from extras import utils

logging.basicConfig(
    format="[%(asctime)s] [%(levelname)s:%(name)s] %(message)s", level=logging.INFO
)

class subcontext(commands.Context):

    async def send(self, content=None, *, tts=False, embed=None, file=None, files=None, delete_after=None, nonce=None):
        """Subclassed send to have all 2000+ chars in file"""
        if content and len(str(content)) > 2000:
            await self.message.add_reaction("\N{OPEN MAILBOX WITH RAISED FLAG}")
            return await utils.paginate(content, self.author)
        return await super().send(content=content, tts=tts, embed=embed, file=file, files=files, delete_after=delete_after)

    async def check(self, message = None):
        await self.message.add_reaction("glowacheck:536720140025200641")
        if message:
            await self.send(message)

    @property
    def created_at(self):
        return self.message.created_at

class DiscordChan(commands.AutoShardedBot):

    def __init__(self):
        super().__init__(
            command_prefix=self.get_prefix,
            case_insensitive=True,
            reconnect=True
        )
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

    async def get_pic(self, url):
        """Takes a url and returns a discord.File"""
        async with self.session.get(url) as rsp:
            init_bytes = await rsp.read()
        return discord.File(init_bytes, filename='picture.png')

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

    @presence_cycle.before_loop()
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

    async def is_owner(self, member):
        return member.id in self.owners

    async def on_ready(self):
        await self.connect_db()
        await self.load_prefixes()
        await self.load_mods()
        self.logger.info("Bot ready")

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

    async def load_mods(self):
        for ext in os.listdir('cogs'):
            try:
                if not ext.endswith(".py"):
                    continue
                self.load_extension(f"cogs.{ext.replace('.py', '')}")
                self.logger.info(f"Loaded {ext}")
            except:
                self.logger.critical(f"{ext} failed:\n{traceback.format_exc()}")

    def run(self):
        super().run(self.settings['token'])

    async def get_context(self, message, cls = None):
        return await super().get_context(message, cls = cls or subcontext)

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

DiscordChan().run()

# hellow~~ owo
