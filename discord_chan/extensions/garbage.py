import re

import discord
from discord.ext import commands

import discord_chan


loli_filter = re.compile(r"\?tags=(\w|\+)*loli([^a-zA-Z]|$)?")


class Garbage(commands.Cog):
    def __init__(self, bot: discord_chan.DiscordChan) -> None:
        super().__init__()
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def block_olaf_lolis(self, message: discord.Message):
        if message.guild is None:
            return

        # wizspoil
        if message.guild.id != 1015677559020724264:
            return

        # anti-olaf
        if len(list(loli_filter.finditer(message.content))) > 0:
            return await message.delete()

        content = message.content.lower()

        # anti-vale
        if any(
            [
                "starr" in content and "furry" in content,
                "fox" in content and "furry" in content,
            ]
        ):
            if content == "starr is not a furry":
                return

            if await self.bot.is_owner(message.author):
                return

            if not isinstance(message.channel, discord.TextChannel):
                return

            hook: discord.Webhook | None = None

            for maybe_hook in await message.channel.webhooks():
                if maybe_hook.token is not None:
                    hook = maybe_hook
                    break

            if hook is None:
                hook = await message.channel.create_webhook(name="GamerHook")

            return await hook.send(
                f"I'm a furry",
                avatar_url=message.author.display_avatar.url,
                username=message.author.display_name,
            )


async def setup(bot: discord_chan.DiscordChan):
    await bot.add_cog(Garbage(bot))
