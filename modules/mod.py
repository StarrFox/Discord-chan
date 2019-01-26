import discord
from discord.ext import commands
from extras import checks
import asyncio
import typing

class mod:

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def prefix(self, ctx):
        """List and add/remove your prefixes"""
        guild = ctx.guild
        if guild.id in self.bot.prefixes:
            e = discord.Embed(
                description="\n".join(self.bot.prefixes[guild.id]),
                color=discord.Color.blurple()
            )
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

    @commands.command()
    @checks.serverowner_or_permissions(manage_messages=True)
    async def purge(self, ctx, number: int, user: typing.Optional[discord.Member] = None, *, text: str = None):
        """Purges messages from certain user or certain text"""
        channel = ctx.message.channel
        number += 1
        if not user and not text:
            try:
                deleted = await channel.purge(limit=number)
                msg = await channel.send(f"Deleted {len(deleted)} messages (deleted invoke message also)")
            except:
                msg = await channel.send("Unable to delete messages")
            await asyncio.sleep(5)
            try:
                await msg.delete()
            except:
                pass
            return
        def msgcheck(msg):
            if user and text:
                if text in msg.content.lower() and msg.author == user:
                    return True
                else:
                    return False
            if user:
                if msg.author == user:
                    return True
            if text:
                if text in msg.content.lower():
                    return True
        deleted = await channel.purge(limit=number, check=msgcheck)
        msg = await channel.send(f'Deleted {len(deleted)} message(s)')
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except:
            pass

    @commands.command()
    @checks.serverowner_or_permissions(manage_messages=True)
    async def clean(self, ctx, num: int = 20):
        if num > 100:
            return await ctx.send("Use purge for deleting more than 100 messages")
        def check(msg):
            return msg.author.id == msg.guild.me.id
        await ctx.channel.purge(
            limit = num,
            check = check,
            bulk = False
        )
        try:
            await ctx.message.add_reaction("\u2705")
        except:
            pass

def setup(bot):
    bot.add_cog(mod(bot))