import discord
import asyncio
import dbl
import json
import traceback

class events:

    def __init__(self, bot):
        self.bot = bot
        try:
            with open("misc_tokens.json") as fo:
                self.tokens = json.load(fo)
                fo.close()
        except:
            pass
        self.dbl_client = dbl.Client(self.bot, self.tokens['dbl'])
        self.tasks = []

    async def on_message(self, message):
        """Handles all incoming messages"""
        return

    async def on_message_edit(self, before, after):
        if not after.embeds:
            await self.bot.process_commands(after)

    async def on_guild_join(self, guild):
        self.bot.prefixes[guild.id] = []
        self.bot.prefixes[guild.id].append('dc!')

    async def on_guild_remove(self, guild):
        self.bot.prefixes.pop(guild.id)

    async def start_dbl(self, time):
        """Starts our dbl and bots.gg events"""
        #This one is disabled until we get verifed
        self.tasks.append(self.bot.loop.create_task(self.dbl(time)))
        #self.tasks.append(self.bot.loop.create_task(self.botsgg(time)))
        self.tasks.append(self.bot.loop.create_task(self.boats(time)))

    async def stop_dbl(self):
        """Stops out dbl and bots.gg events"""
        for task in self.tasks:
            task.cancel()
        self.tasks = []

    async def dbl(self, time):
        """Updates DBl guild stats"""
        while not self.bot.is_closed():
            try:
                await self.dbl_client.post_server_count()
                self.bot.logger.info(f"Sent {len(self.bot.guilds)} to DBL")
            except:
                self.bot.logger.error(f"DBL updated failed\n{traceback.format_exc()}")
                pass
            await asyncio.sleep(time)

    async def botsgg(self, time):
        """Updates discord.bots.gg guild stats
        
        No api so we'll have to make our own request"""
        while not self.bot.is_closed():
            headers = {
                "Authentication": self.tokens['bots.gg'],
                "Content-Type": "application/json"
            }
            subcount = {
                "guildCount": len(self.bot.guilds)
            }
            try:
                await self.bot.session.post(
                    f"https://discord.bots.gg/api/v1/bots/{self.bot.user.id}/stats",
                    headers = headers,
                    json = subcount
                )
            except:
                pass
            await asyncio.sleep(1800)

    async def boats(self, time):
        """Updates discord.boats guild count"""
        while not self.bot.is_closed():
            heads = {
                "Authentication": self.tokens['boats'],
                "Content-Type": "application/json"
            }
            guild_count = {
                "server_count": len(self.bot.guilds)
            }
            try:
                await self.bot.session.post(
                    f"https://discord.boats/api/bot/{self.bot.user.id}",
                    headers = heads,
                    json = guild_count
                )
            except:
                pass
            await asyncio.sleep(time)

def setup(bot):
    bot.add_cog(events(bot))