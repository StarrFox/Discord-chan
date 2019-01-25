from discord.ext import commands
import discord.utils

def is_owner_check(ctx):
    id = ctx.message.author.id
    return id in ctx.bot.owners

def is_owner():
    return commands.check(is_owner_check)

def check_permissions(ctx, perms):
    if is_owner_check(ctx):
        return True
    elif not perms:
        return False

    ch = ctx.message.channel
    author = ctx.message.author
    resolved = ch.permissions_for(author)
    return all(getattr(resolved, name, None) == value for name, value in perms.items())

def has_permissions(ctx, perms):
    if is_owner_check(ctx):
        return True
    elif not perms:
        return False

    ch = ctx.message.channel
    author = ctx.message.author
    resolved = ch.permissions_for(author)
    return all(getattr(resolved, name, None) == value for name, value in perms.items())

def role_or_permissions(ctx, check, **perms):
    if check_permissions(ctx, perms):
        return True

    ch = ctx.message.channel
    author = ctx.message.author
    if ch.is_private:
        return False

    role = discord.utils.find(check, author.roles)
    return role is not None

def serverowner_or_permissions(**perms):
    def predicate(ctx):
        if ctx.message.guild is None:
            return False
        server = ctx.message.guild
        owner = server.owner

        if ctx.message.author.id == owner.id:
            return True

        return check_permissions(ctx,perms)
    return commands.check(predicate)

def serverowner():
    def predicate(ctx):
        if ctx.guild is None:
            return False
        guild = ctx.guild
        owner = guild.owner

        if ctx.message.author.id == owner.id:
            return True

        return is_owner_check(ctx)
    return commands.check(predicate)