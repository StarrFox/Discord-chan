from discord.ext import commands
import discord
import datetime
from extras import utils

#Checks for commands
async def is_nubby_or_owner(ctx):
    return await ctx.bot.is_owner(ctx.author) or ctx.author.id == 176796254821548033

async def is_above_mod(ctx):
    mod_role = ctx.bot.get_guild(390607785437691916).get_role(396797202779078657)
    return ctx.author.top_role.position >= mod_role.position

async def above_mod(member):
    mod_role = member.guild.get_role(396797202779078657)
    return member.top_role.position >= mod_role.position

class nubby(commands.Cog):
    """
    Set of commands and events for Nubby's guild
    """

    def __init__(self, bot):
        self.bot = bot
        self.guild = bot.get_guild(390607785437691916)

    async def cog_check(self, ctx):
        return ctx.guild == self.guild

    @commands.command()
    async def cool(self, ctx, member: discord.Member = None):
        if not member:
            member = self.guild.get_member(204600313485852672)
        await ctx.send(f"Thanks {member.display_name}, very cool!")

    @commands.command()
    async def laval(self, ctx):
        await ctx.send("You miserable ungrateful piss ants! How dare you insects go after me!")

    @commands.command()
    @commands.check(is_above_mod)
    async def twoweeks(self, ctx):
        target_roles = [self.guild.get_role(i) for i in [501092781473792020, 501092781473792020]]
        processed = [] #Returned positive
        for member in self.guild.members:
            checks = [
                member.bot,
                target_roles[0] in member.roles or target_roles[1] in member.roles,
                not member.joined_at + datetime.timedelta(weeks=2) < datetime.datetime.utcnow()
            ]
            if any(checks):
                return
            processed.append(member)
        msg = "Members that need the roles:\n"+"\n".join([i.name for i in processed])
        await utils.paginate(msg, ctx)
        target_msg = await ctx.send("React with \N{HEAVY PLUS SIGN} to add their roles, one by one #Nubbyfied")
        await target_msg.add_reaction("\N{HEAVY PLUS SIGN}")
        while len(processed) != 0:
            def check(r, u):
                checks = [
                    await above_mod(u),
                    r.message.id == target_msg.id,
                    str(r) == "\N{HEAVY PLUS SIGN}"
                ]
                return all(checks)
            try:
                self.bot.wait_for("reaction_add", check=check, timeout=300)
                target = processed[-1]
                for role in target_roles:
                    await target.add_roles(role)
                await ctx.send(f"Added {target.name}'s roles")
                processed.remove(target)
            except:
                await ctx.send("Timed out")
                break
        await ctx.send("All roles added")

def setup(bot):
    bot.add_cog(nubby(bot))
