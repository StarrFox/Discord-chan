import json
import typing
import asyncio
import discord

from PIL import Image
from os import system
from io import BytesIO
from extras import utils
from discord.ext import commands
from imagehash import phash, hex_to_hash

bool_dict = {
    "true": True,
    "on": True,
    "1": True,
    "false": False,
    "off": False,
    "0": False
}

POKECORD_ID = 365975655608745985

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

    def __init__(self, bot):
        self.bot = bot
        self.hashmap = self.get_hashmap()
        self.pokecord_tasks = {}

    def get_hashmap(self):
        with open("hashmap.json") as fp:
            unhashed = json.load(fp)
        hashmap = {}
        for name, hex_code in unhashed.items():
            hashmap[name] = hex_to_hash(hex_code)
        return hashmap

    async def cog_check(self, ctx):
        if not await self.bot.is_owner(ctx.author):
            raise commands.NotOwner('You do not own this bot.')
        return True

    @commands.command()
    async def dm(self, ctx, user: discord.User, *, msg: str):
        await user.send(msg)
        await ctx.send("message sent")

    @commands.command()
    async def restart(self, ctx):
        await ctx.send("😡")
        await self.bot.logout()

    @commands.command()
    async def noprefix(self, ctx, toggle: bool = None):
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
    async def loadjsk(self, ctx):
        self.bot.load_extension('bot_stuff.jsk', **self.jsk_settings)
        await ctx.send('Loaded jsk')

    @commands.command()
    async def jskset(self, ctx, item: typing.Optional[str] = None, value: str = None):
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
        return phash(img)

    async def get_best_match(self, url: str):
        looking_for_hash = await self.convert_to_hash(url)
        diff_map = {}
        for name, hash_code in self.hashmap.items():
            diff_map[name] = looking_for_hash - hash_code
        return sorted(diff_map.items(), key=lambda i: i[1])[:1]

    def is_spawn(self, message: discord.Message):
        try:
            return message.embeds[0].image.url.endswith('PokecordSpawn.jpg')
        except:
            return False

    async def pokecord_task(self, channel_id: int):
        while True:
            def check(message):
                checks = [
                    message.channel.id == channel_id,
                    message.author.id == POKECORD_ID,
                    self.is_spawn(message)
                ]
                return all(checks)
            message = await self.bot.wait_for('message', check=check)
            best_matches = await self.get_best_match(
                message.embeds[0].image.url
            )
            await message.channel.send(f"`p!catch {best_matches[0][0]}` or `p!catch {best_matches[0][0]}`")

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
