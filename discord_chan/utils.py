# -*- coding: utf-8 -*-
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

bool_dict = {
    "true": True,
    "on": True,
    "1": True,
    "false": False,
    "off": False,
    "0": False
}

async def msg_resend(destination: discord.abc.Messageable, msg: discord.Message) -> discord.Message:
    """
    Resend a message
    :param destination: Where to send the message
    :param msg: The Message to send
    :return: The Message sent
    """
    return await destination.send(
        content=msg.content,
        tts=msg.tts,
        embed=msg.embeds[0] if msg.embeds else None,
        files=[attachment.to_file() for attachment in msg.attachments]
    )


def msg_jsonify(message: discord.Message) -> dict:
    """
    Converts a Message to dict representation
    This is the same as what Discord sends
    :param message: The Message to convert
    :return:
    """
    data = {
        "id": str(message.id),
        "type": message.type.value,
        "content": message.content,
        "author": {
            "id": str(message.author.id),
            "username": message.author.name,
            "avatar": message.author.avatar,
            "discriminator": message.author.discriminator,
            "bot": message.author.bot
        },
        "attachments": [],
        "embeds": [e.to_dict() for e in message.embeds],
        "mentions": [],
        "mention_roles": [],
        "pinned": message.pinned,
        "mention_everyone": message.mention_everyone,
        "tts": message.tts,
        "timestamp": str(message.created_at),
        "edited_timestamp": str(message.edited_at),
        "flags": message.flags
    }
    return data
