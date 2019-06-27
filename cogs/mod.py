import discord
from discord.ext import commands
from extras import checks
import asyncio
import typing

def is_above(invoker, user):
    return invoker.top_role > user.top_role

class mod(commands.Cog):
    """Moderation commands"""

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
        if guild.id in self.bot.prefixes:
            if prefix in self.bot.prefixes[guild.id]:
                return await ctx.send("Prefix already added")
            if len(self.bot.prefixes[guild.id]) >= 20:
                return await ctx.send('Can only have 20 prefixes, remove one to add this one')
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
        try:
            await ctx.message.delete()
        except:
            pass
        if not user and not text:
            try:
                deleted = await channel.purge(limit=number)
                await channel.send(f"Deleted {len(deleted)} messages (deleted invoke message also)", delete_after=5)
            except:
                await channel.send("Unable to delete messages", delete_after=5)
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
        await channel.send(f'Deleted {len(deleted)} message(s)', delete_after=5)

    @commands.command()
    async def clean(self, ctx, num: int = 20):
        """Clean's up the bot's messages"""
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

    @commands.command()
    @checks.serverowner_or_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason = None):
        """
        Bans a member
        """
        if not is_above(ctx.author, member):
            return await ctx.send("You can't ban someone with a higher role")
        try:
            await member.ban(reason=reason)
            await ctx.send(f"{member.name} was banned")
        except:
            await ctx.send("I couldn't ban them :c")

    @commands.command()
    @checks.serverowner_or_permissions(ban_members=True)
    async def hackban(self, ctx, id: int, *, reason = None):
        """
        Bans using an id
        """
        if ctx.guild.get_member(id):
            return await ctx.send(f"This id belongs to a member use {ctx.prefix}ban for this")
        try:
            await ctx.guild.ban(discord.Object(id=id), reason=reason)
            await ctx.send(f"Banned {id}")
        except:
            await ctx.send("I couldn't ban them :c")

    @commands.command()
    @checks.serverowner_or_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason = None):
        """
        Kicks a member
        """
        if not is_above(ctx.author, member):
            return await ctx.send("You can't kick someone with a higher role")
        try:
            await member.kick(reason=reason)
            await ctx.send(f"{member.name} has been kicked")
        except:
            await ctx.send("I was unable to kick them")

    @commands.command()
    @checks.serverowner_or_permissions(manage_emojis=True)
    async def emoji(self, ctx, name, link):
        """Creates an emoji"""
        async with self.bot.session.get(link) as res:
            try:
                await ctx.guild.create_custom_emoji(name=name, image=await res.read())
                await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
            except Exception as e:
                if isinstance(e, discord.errors.Forbidden):
                    return await ctx.send("I dont have the perms to add emojis")
                elif isinstance(e, discord.errors.HTTPException):
                    return await ctx.send("File too large")
                await ctx.send(e)

def setup(bot):
    bot.add_cog(mod(bot))
