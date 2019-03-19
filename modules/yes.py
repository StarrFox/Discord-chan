from discord.ext import commands

class Yes(commands.Cog):

<<<<<<< HEAD
    @commands.command()
=======
>>>>>>> 6089ca0fba2cfcd678963f0bae31ff701b340b18
    async def epic(self, ctx):
        """Epic"""
        await ctx.send("Epic:sunglasses:")

def setup(bot):
    bot.add_cog(Yes())
