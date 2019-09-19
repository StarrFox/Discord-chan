from discord.ext import commands
import discord

from PIL import Image, ImageSequence
from math import sqrt
from io import BytesIO
from tarfile import TarFile, TarInfo
from functools import partial

class wallemojis(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def make_emojis(self, img, name: str, wall_size: tuple, gif: bool):
        width, height = img.size
        final = wall_size[0]*wall_size[1]
        per_emoji = (width*height)//final
        emoji_size = round(sqrt(per_emoji))
        w_fac = emoji_size 
        h_fac = emoji_size
        new_w = (width//w_fac)*w_fac
        new_h = (height//h_fac)*h_fac
        emojis = []
        if gif:
            for row in range(int(new_h/h_fac)):
                for collum in range(int(new_w/w_fac)):
                    frames = []
                    for page in ImageSequence.Iterator(img):
                        page = page.resize((new_w, new_h))
                        width_cord = 0+(w_fac*collum)
                        height_cord = h_fac*row
                        frames.append(page.crop((width_cord, height_cord, width_cord+w_fac, height_cord+h_fac)))
                    emojis.append(frames)
            return self.zip_gif_emojis(emojis, name, int(img.width/w_fac), int(img.height/h_fac))
        else:
            img = img.resize((new_w, new_h))
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

    def zip_gif_emojis(self, emojis: list, name: str, c_size: int, r_size: int):
        """
        same as normal but emojis is a list of frame lists
        """
        fp = BytesIO()
        zip = TarFile(mode='w', fileobj=fp)
        for idx, emoji in enumerate(emojis):
            f = BytesIO()
            emoji[0].save(f, "gif", append_images=emoji[1:], save_all=True, loop=0)
            f.seek(0)
            info = TarInfo(f"{name}_{idx}.gif")
            info.size = len(f.getbuffer())
            zip.addfile(info, fileobj=f)
        fp.seek(0)
        return fp

    async def get_bytes(self, link):
        async with self.bot.session.get(link) as res:
            return (await res.read(), res.content_type)

    @commands.command()
    @commands.cooldown(1, 30, commands.cooldowns.BucketType.user)
    async def wallemoji(self, ctx, name, width: int, height: int, link):
        """
        Makes some emojis from an image
        """
        if not 0 < height <= 10 or not 0 < width <= 10:
            return await ctx.send("plz only use sizes between 0 and 10")
        width, height = (round(width), round(height))
        _bytes, file_type = await self.get_bytes(link)
        if not "image" in file_type.lower():
            return await ctx.send("Link was not to an image")
        gif = "gif" in file_type.lower()
        img = Image.open(BytesIO(_bytes))
        func = partial(self.make_emojis, img, name, (width, height), gif)
        archive = await self.bot.loop.run_in_executor(None, func)
        await ctx.send(file=discord.File(archive, filename=f"{name}.tar"))

def setup(bot):
    bot.add_cog(wallemojis(bot))