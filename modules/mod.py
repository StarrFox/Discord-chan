import discord
from discord.ext import commands
from extras import checks

class mod:

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def prefix(self, ctx):
        """List and add/remove your prefixes"""
        guild = ctx.guild
        if guild.id in self.bot.prefixes:
            e = discord.Embed(description="\n".join(self.bot.prefixes[guild.id]), color=discord.Color.dark_purple())
            await ctx.send(embed=e)
        else:
            await ctx.send('exe!')

    @prefix.command()
    @checks.serverowner_or_permissions(administrator=True)
    async def add(self, ctx, prefix: str):
        """Add a prefix for this server"""
        guild = ctx.guild
        if len(prefix) > 20:
            return await ctx.send("Prefix too long (max is 20 chars)")
        if guild.id in self.bot.prefixes:
            if len(self.bot.prefixes[guild.id]) >= 10:
                return await ctx.send('Can only have 10 prefixes, remove one to add this one')
            else:
                self.bot.prefixes[guild.id].append(prefix)
                await ctx.send("Prefix added")
        else:
            self.bot.prefixes[guild.id] = []
            self.bot.prefixes[guild.id].append(prefix)
            await ctx.send("Prefix added")

    @prefix.command(aliases=['rem'])
    @checks.serverowner_or_permissions(administrator=True)
    async def remove(self, ctx, prefix: str):
        """Remove a prefix for this server"""
        guild = ctx.guild
        if guild.id in self.bot.prefixes:
            if len(self.bot.prefixes[guild.id]) == 1:
                return await ctx.send("Sorry I can't have no prefix")
            else:
                if prefix in self.bot.prefixes[guild.id]:
                    self.bot.prefixes[guild.id].remove(prefix)
                    return await ctx.send("Prefix removed")
                else:
                    return await ctx.send("Prefix not found")
        else:
            await ctx.send("Don't know how you got here lol")

def setup(bot):
    bot.add_cog(mod(bot))