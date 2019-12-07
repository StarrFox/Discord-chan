#  Copyright © 2019 StarrFox
#  #
#  Discord Chan is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  #
#  Discord Chan is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#  #
#  You should have received a copy of the GNU Affero General Public License
#  along with Discord Chan.  If not, see <https://www.gnu.org/licenses/>.

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
        except RuntimeError:
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
