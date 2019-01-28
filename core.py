import discord
from discord.ext import commands
import asyncio
import json
import os
from datetime import datetime
import asyncpg

class subcontext(commands.Context):

    async def check(self, message = None):
        await self.message.add_reaction("\u2705")
        if message:
            await self.send(message)

    @property
    def when(self):
        return self.message.created_at

class DiscordChan(commands.AutoShardedBot):

    def __init__(self):
        with open('settings.json') as tf:
            self.settings = json.load(tf)
            tf.close()
        self.owners = [
            285148358815776768
        ]
        self.db = None
        self.prefixes = {}
        self.uptime = datetime.now()
        super().__init__(
            command_prefix=self.get_prefix,
            case_insensitive=True,
            reconnect=True
        )
        self.add_command(self.loadjsk)
        self.loop.create_task(self.presence_loop(300))

    @commands.command()
    @commands.is_owner()
    async def loadjsk(self, ctx):
        self.load_extension('jishaku')
        await ctx.send('Loaded jsk')

    @commands.command(name='help')
    async def _help(self, ctx, command: str):
        """Shows this command"""
        return

    async def presence_loop(self, time):
        await self.wait_until_ready()
        toggle = True
        while True:
            if toggle:
                prez = f"dc!help | {len(self.guilds)} servers"
                toggle = False
            else:
                prez = f"dc!help | {len(self.users)} users"
                toggle = True
            await self.change_presence(activity=discord.Game(prez))
            await asyncio.sleep(time)

    async def get_prefix(self, message):
        if not message.guild:
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
        print("Connected as:")
        print(f"User: {self.user}")
        print(f"ID: {self.user.id}")
        print(f"With {len(self.commands)} cmds loaded")

    async def connect_db(self):
        self.db = await asyncpg.connect(
            'postgresql://postgres@localhost/discordchan',
            password=self.settings['db_pass']
        )

    async def load_prefixes(self):
        for guild_id, prefix_list in await self.db.fetch("SELECT * FROM prefixes;"):
            self.prefixes[guild_id] = prefix_list
            print("Prefixes loaded")

    async def unload_prefixes(self):
        await self.db.execute("DELETE FROM prefixes;")
        await self.db.executemany("INSERT INTO prefixes(guild_id, prefixes) VALUES ($1, $2)", self.prefixes.items())

    async def load_mods(self):
        self.load_extension('jishaku')
        loaded = []
        failed = []
        for ext in os.listdir('modules'):
            try:
                if not ext.endswith(".py"):
                    continue
                self.load_extension(f"modules.{ext.replace('.py', '')}")
                loaded.append(ext.replace('.py', ''))
            except Exception as e:
                failed.append(ext.replace('.py', ''))
                print(e)
        print(f"Loaded: {loaded}")
        print(f"Failed: {failed}")

    def run(self):
        super().run(self.settings['token'])

    async def get_context(self, message):
        return await super().get_context(message, cls=subcontext)

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
