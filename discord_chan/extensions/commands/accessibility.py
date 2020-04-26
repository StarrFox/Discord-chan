# -*- coding: utf-8 -*-
#  Copyright © 2020 StarrFox
#
#  Discord Chan is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Discord Chan is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with Discord Chan.  If not, see <https://www.gnu.org/licenses/>.

import re
from io import BytesIO

import discord
from aioec import EmoteExists
from discord.ext import commands, flags

from discord_chan import (ImageUrlConverter, ImageUrlDefault, DiscordChan, get_bytes, SubContext)

CUSTOM_EMOJI_REGEX = r'<(?P<animated>a)?:(?P<name>[0-9a-zA-Z_]{2,32}):(?P<id>[0-9]{15,21})>'


class Accessibility(commands.Cog, name='accessibility'):

    def __init__(self, bot: DiscordChan):
        self.bot = bot

    @commands.command()
    async def sendlink(self, ctx: commands.Context, thing: ImageUrlConverter = ImageUrlDefault):
        """
        Sends the link of a member, custom emoji, message attachment, message embed, or repeats a link.
        idk why you would use the last one
        """
        thing: str
        await ctx.send(thing)

    @commands.command(aliases=['popembed'])
    async def sendfile(self, ctx: SubContext, thing: ImageUrlConverter = ImageUrlDefault):
        """
        Sends the image file of a member, custom emoji, message attachment or message embed
        """
        thing: str
        res = await get_bytes(thing, max_length=8)

        buffer = BytesIO(res.file_bytes)

        file = discord.File(buffer, 'popped.png')
        await ctx.send(file=file, no_edit=True)

    # # Todo: finish
    # @commands.command(name='embed-to-text', aliases=['ett'])
    # async def embed_to_text(self, ctx: commands.Context, embed: EmbedConverter = EmbedDefault):
    #     """
    #     Converts an embed to text format.
    #     """
    #     embed: discord.Embed
    #     data = embed.to_dict()
    #
    #     res = []
    #
    #     for key, value in data.items():
    #         res.append(f'{key}: {value!s}')
    #
    #     await ctx.send('\n'.join(res))

    @flags.add_flag('--to-ec', action='store_true', default=False)
    @flags.command(name='steal-these')
    async def steal_these(self, ctx: SubContext, message: discord.Message, **options):
        """
        "Steal" the custom emojis from a message
        pass --to-ec to upload to Emote Collector
        """
        if options['to_ec'] and not self.bot.ec:
            return await ctx.send('Emotecollector api is not enabled.')

        emojis = []

        for group in re.finditer(CUSTOM_EMOJI_REGEX, message.content):
            groups = group.groups()
            emojis.append(
                discord.PartialEmoji(
                    animated=bool(groups[0]),
                    name=groups[1],
                    id=groups[2]
                )
            )

        if not emojis:
            return await ctx.send('No custom emojis found in message.')

        if options['to_ec']:
            for emoji in emojis:
                try:
                    await self.bot.ec.create(
                        name=emoji.name,
                        url=str(emoji.url)
                    )

                    await ctx.send(f'Emote {emoji.name} added to EmoteCollector.', no_edit=True)

                except EmoteExists:
                    await ctx.send(f'Emote named {emoji.name} already exists in EmoteCollector.', no_edit=True)

        else:
            await ctx.send(
                '\n'.join([f'{e.name}: <{e.url!s}>' for e in emojis])
            )


def setup(bot: DiscordChan):
    bot.add_cog(Accessibility(bot))
