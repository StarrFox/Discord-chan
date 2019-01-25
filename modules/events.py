import discord
import asyncio

class events:

    def __init__(self, bot):
        self.bot = bot

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

def setup(bot):
    bot.add_cog(events(bot))