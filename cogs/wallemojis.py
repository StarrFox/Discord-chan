from discord.ext import commands
import discord

from PIL import Image
from math import sqrt
from io import BytesIO
from tarfile import TarFile, TarInfo
from functools import partial

class wallemojis(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def make_emojis(self, img, name: str, wall_size: tuple = (8, 8)):
        width, height = img.size
        final = wall_size[0]*wall_size[1]
        per_emoji = (width*height)//final
        emoji_size = round(sqrt(per_emoji))
        w_fac = emoji_size 
        h_fac = emoji_size
        new_w = (width//w_fac)*w_fac
        new_h = (height//h_fac)*h_fac
        img = img.resize((new_w, new_h))
        emojis = []
        for row in range(int(img.height/h_fac)):
            for collum in range(int(img.width/w_fac)):
                width_cord = 0+(w_fac*collum)
                height_cord = h_fac*row
                crop = img.crop((width_cord, height_cord, width_cord+w_fac, height_cord+h_fac))
                emojis.append(crop)
        return self.zip_emojis(emojis, name, int(img.width/w_fac), int(img.height/h_fac))

    def zip_emojis(self, emojis: list, name: str, c_size: int, r_size: int):
            fp = BytesIO()
            zip = TarFile(mode='w', fileobj=fp)
            for idx, emoji in enumerate(emojis):
                    f = BytesIO()
                    emoji.save(f, "png")
                    f.seek(0)
                    info = TarInfo(f"{name}_{idx}.png")
                    info.size = len(f.getbuffer())
                    zip.addfile(info, fileobj=f)
            fp.seek(0)
            return fp

    async def get_bytes(self, link):
        async with self.bot.session.get(link) as res:
            if res.content_type != "image/webp":
                return None
            return await res.read()

    @commands.command()
    @commands.cooldown(1, 30, commands.cooldowns.BucketType.user)
    async def wallemoji(self, ctx, name, size: int, link):
        """
        Makes some emojis from an image
        """
        if not 0 < size < 10:
            return await ctx.send("plz only use sizes between 0 and 10")
        size = round(size)
        _bytes = await self.get_bytes(link)
        if _bytes is None:
            return await ctx.send("Link was not to an image")
        img = Image.open(BytesIO(_bytes))
        func = partial(self.make_emojis, img, name, (size, size))
        archive = await self.bot.loop.run_in_executor(None, func)
        await ctx.send(file=discord.File(archive, filename=f"{name}.tar"))

def setup(bot):
    bot.add_cog(wallemojis(bot))