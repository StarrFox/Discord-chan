import discord
from discord.ext.commands import Cog

class Patches(Cog):
    """Lib Patches"""

    def __init__(self):
        self.old_send = discord.abc.Messageable.send
        self.patch()

    def cog_unload(self):
        self.un_patch()

    async def box(self, content):
        return await self.send(content=f"```py\n{content}```")

    def patch(self):
        discord.abc.Messageable.box = self.box

    def un_patch(self):
        del discord.abc.Messageable.box

def setup(bot):
    bot.add_cog(Patches())
