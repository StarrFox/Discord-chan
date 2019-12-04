from discord.ext import commands

def is_owner():
    async def predicate(ctx):
        if await ctx.bot.is_owner(ctx.author):
            return True
        raise commands.NotOwner()
    return commands.check(predicate)

def has_permissions(**perms):
    async def predicate(ctx):
        ch = ctx.channel
        permissions = ch.permissions_for(ctx.author)
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm, None) != value]
        if not missing or await ctx.bot.is_owner(ctx.author):
            return True
        raise commands.MissingPermissions(missing)
    return commands.check(predicate)

def guildowner():
    async def predicate(ctx):
        if ctx.guild is None:
            return False
        elif ctx.message.author == ctx.guild.owner:
            return True
        elif await ctx.bot.is_owner(ctx.author):
            return True
        raise commands.MissingPermissions(["Guild owner"])
    return commands.check(predicate)