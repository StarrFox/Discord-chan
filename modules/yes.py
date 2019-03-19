from discord.ext import commands

class Yes(commands.Cog):

    @commands.command()
    async def epic(self, ctx):
        """Epic"""
        await ctx.send("Epic:sunglasses:")

def setup(bot):
    bot.add_cog(Yes())
