from discord.ext import commands
import discord.utils

def owner_check(ctx):
    id = ctx.message.author.id
    return id in ctx.bot.owners

def is_owner():
    def predicate(ctx):
        if owner_check(ctx):
            return True
        raise commands.NotOwner()
    return commands.check(predicate)

def has_permissions(**perms):
    def predicate(ctx):
        ch = ctx.channel
        permissions = ch.permissions_for(ctx.author)
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm, None) != value]
        if not missing or owner_check(ctx):
            return True
        raise commands.MissingPermissions(missing)
    return commands.check(predicate)

def guildowner():
    def predicate(ctx):
        if ctx.guild is None:
            return False
        elif ctx.message.author == ctx.guild.owner:
            return True
        elif owner_check(ctx):
            return True
        raise commands.MissingPermissions("Server Owner")
    return commands.check(predicate)