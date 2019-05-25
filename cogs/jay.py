from discord.ext import commands

import random

class jay(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.laval = bot.get_cog("nubby").laval_quotes

    async def jays_laval(self, des):
        await des.send(random.choice(self.laval))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == 145897775274524672 and message.content == "dc!laval":
            await self.jays_laval(message.channel)

def setup(bot):
    bot.add_cog(jay(bot))
