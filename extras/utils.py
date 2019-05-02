import discord
from discord.ext import commands

def block(content, lang='py'):
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

async def msg_resend(msg: discord.Message, destination):
    if len(msg.content) == 0: content = None
    else: content = msg.content
    try: embed = msg.embeds[0]
    except: pass
    await destination.send(
        content,
        embed=embed,
    )
