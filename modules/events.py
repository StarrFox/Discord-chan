import discord
import asyncio
import dbl

class events:

    def __init__(self, bot):
        self.bot = bot
        try:
            self.dbl_client = dbl.Client(self.bot, self.bot.settings['dbltoken'])
            self.bot.loop.create_task(self.dbl())
        except:
            pass

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

    async def dbl(self):
        """Updates DBl guild stats"""
        while not self.bot.is_closed():
            try:
                await self.dbl_client.post_server_count()
            except:
                pass
            await asyncio.sleep(1800)

def setup(bot):
    bot.add_cog(events(bot))