#  Copyright © 2019 StarrFox
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

import json
import typing
from io import BytesIO

import discord
from PIL import Image
from discord.ext import commands
from imagehash import phash, hex_to_hash

from extras import utils

bool_dict = {
    "true": True,
    "on": True,
    "1": True,
    "false": False,
    "off": False,
    "0": False
}

POKECORD_ID = 365975655608745985


def get_hashmap():
    with open("hashmap.json") as fp:
        unhashed = json.load(fp)
    hashmap = {}
    for name, hex_code in unhashed.items():
        hashmap[name] = hex_to_hash(hex_code)
    return hashmap


def is_spawn(message: discord.Message):
    try:
        return message.embeds[0].image.url.endswith('PokecordSpawn.jpg')
    except IndexError:
        return False


class owner(commands.Cog):
    """Owner commands"""

    jsk_settings = {
            "task": "<a:sonic:577005444191485952>",
            "done": "<a:dancin:582409853918511165>",
            "syntax": "<a:default:577017740016222229>",
            "timeout": "error:539157627385413633",
            "error": "<a:default:577017740016222229>",
            "tracebacks": "\N{BLACK DOWN-POINTING DOUBLE TRIANGLE}",
            "scope_prefix": "",
            "retain": True,
            "bot_level_cmds": False,
            "channel_tracebacks": True
        }

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.hashmap = get_hashmap()
        self.pokecord_tasks = {}

    async def cog_check(self, ctx: commands.Context):
        if not await self.bot.is_owner(ctx.author):
            raise commands.NotOwner('You do not own this bot.')
        return True

    @commands.command()
    async def dm(self, ctx: commands.Context, user: discord.User, *, msg: str):
        await user.send(msg)
        await ctx.send("message sent")

    @commands.command()
    async def restart(self, ctx: commands.Context):
        await ctx.send("Restarting.")
        await self.bot.logout()

    @commands.command()
    async def noprefix(self, ctx: commands.Context, toggle: bool = None):
        """Toogles having no prefix"""
        if toggle is None:
            if self.bot.noprefix:
                return await ctx.send("No prefix is currently on.")
            return await ctx.send("No prefix is currently off.")
        if toggle:
            if self.bot.noprefix:
                return await ctx.send("No prefix is already on.")
            self.bot.noprefix = True
            return await ctx.send("No prefix turned on.")
        if not self.bot.noprefix:
            return await ctx.send("No prefix is already off.")
        self.bot.noprefix = False
        return await ctx.send("No prefix turned off.")

    @commands.command()
    async def loadjsk(self, ctx: commands.Context):
        self.bot.load_extension('bot_stuff.jsk', **self.jsk_settings)
        await ctx.send('Loaded jsk')

    @commands.command()
    async def jskset(self, ctx: commands.Context, item: typing.Optional[str] = None, value: str = None):
        if item is None or value is None:
            return await ctx.send(utils.block(json.dumps(self.jsk_settings, indent=4)))
        if isinstance(self.jsk_settings[item], bool):
            self.jsk_settings[item] = bool_dict[value.lower()]
        else:
            self.jsk_settings[item] = value
        await ctx.send("changed")

    async def convert_to_hash(self, url: str):
        file = BytesIO(
            await (await self.bot.session.get(url)).read()
        )
        img = Image.open(file)
        img = img.resize((350, 350))
        return phash(img)

    async def get_best_match(self, url: str):
        looking_for_hash = await self.convert_to_hash(url)
        diff_map = {}
        for name, hash_code in self.hashmap.items():
            diff_map[name] = looking_for_hash - hash_code
        return sorted(diff_map.items(), key=lambda i: i[1])[0][0]

    async def pokecord_task(self, channel_id: int):
        while True:
            def check(msg):
                checks = [
                    msg.channel.id == channel_id,
                    msg.author.id == POKECORD_ID,
                    is_spawn(msg)
                ]
                return all(checks)
            message = await self.bot.wait_for('message', check=check)
            best_match = await self.get_best_match(
                message.embeds[0].image.url
            )
            await message.channel.send(
                f"`p!catch {best_match}`"
            )

    @commands.command()
    async def pokecord(self, ctx: commands.Context):
        channel_id = ctx.channel.id
        if channel_id in self.pokecord_tasks.keys():
            self.pokecord_tasks[channel_id].cancel()
            del self.pokecord_tasks[channel_id]
            await ctx.send("Toggled off")
        else:
            self.pokecord_tasks[channel_id] = self.bot.loop.create_task(
                self.pokecord_task(channel_id)
            )
            await ctx.send("Toggled on")

def setup(bot):
    bot.add_cog(owner(bot))
