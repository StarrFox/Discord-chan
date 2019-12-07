import discord

from discord.ext import commands

def block(content, lang=''):
    """Returns a codeblock"""
    return f"```{lang}\n{content}```"

async def paginate(log, destination):
    """Paginates and sends to a channel"""
    paginator = commands.Paginator()
    while log:
        try:
            paginator.add_line(log)
            log = ''
        except:
            paginator.add_line(log[:1992])
            log = log[1992:]
        for page in paginator.pages:
            await destination.send(page)

async def msg_resend(msg: discord.Message, destination: discord.abc.Messageable):
    try:
        embed = msg.embeds[0]
    except IndexError:
        embed = None
    await destination.send(
        msg.content,
        embed=embed,
    )
