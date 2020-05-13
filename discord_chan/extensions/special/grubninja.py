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

import datetime
from typing import Optional

import aiohttp
import discord
from discord.ext import commands
from terminaltables import AsciiTable

from discord_chan import SubContext, db

GUILD_ID = 608769523637813249
CHANNEL_LOG_ID = 709610148355899463


class Grubninja(commands.Cog, name="grubninja"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # commands

    async def cog_check(self, ctx: commands.Context):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()

        if ctx.guild.id != GUILD_ID:
            raise commands.CheckFailure("GRUB")

        return True

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def grub(self, ctx: commands.Context):
        """Grub base command, status overview"""
        res = await self.get_all_config()

        table_data = [["key", "value"]]
        if res:
            for row in res:
                table_data.append(list(row))
        table = AsciiTable(table_data)

        await ctx.send(f"```\n{table.table}\n```")

    @grub.command(name="emoji")
    async def grub_emoji(self, ctx: SubContext, emoji: discord.Emoji):
        """Sets the current verification emoji; clears old reactions and
        adds new emoji"""
        # remove old emoji and add new one
        message = await self.get_config("message")
        if message:
            split = message.split("-")
            verification_channel = self.bot.get_channel(int(split[0]))
            if not verification_channel:
                return await ctx.send("Verification channel not found.")

            verification_message: discord.Message = await verification_channel.fetch_message(
                int(split[1])
            )
            await verification_message.clear_reactions()
            await verification_message.add_reaction(emoji)

        await self.set_config("emoji", str(emoji.id))
        await ctx.confirm("Emoji set.")

    @grub.command(name="message")
    async def grub_message(self, ctx: SubContext, message: discord.Message):
        """Sets the current verifivation message"""
        emoji = await self.get_config("emoji")
        if emoji:
            # Discord doesn't check names
            await message.add_reaction(f"<:_:{emoji}>")
        await self.set_config("message", f"{message.channel.id}-{message.id}")
        await ctx.confirm("Message set.")

    @grub.command(name="role")
    async def grub_role(self, ctx: SubContext, role: discord.Role):
        """Sets the current verification role"""
        await self.set_config("role", str(role.id))
        await ctx.confirm("Role set.")

    @grub.command(name="status")
    async def grub_status(self, ctx: SubContext, toggle: bool):
        """toggles verification on/off

        [p]grub status on  -> turns verification on
        [p]grub status off -> turns verification off
        """
        await self.set_config("status", str(int(toggle)))
        await ctx.confirm("Status set.")

    @grub.command(name="generate", aliases=["gen"])
    async def grub_generate(self, ctx: SubContext, member: discord.Member):
        """generates a captcha key for a specified user"""

        async def create_customer(member: discord.Member):
            create_customer_payload = {
                "api_token": self.bot.config.extra_tokens.api_token,
                "product_id": self.bot.config.extra_tokens.product_id,
                "first": member.name,
                "last": member.id,
                "email": "default@keyzone.com",
            }
            async with aiohttp.ClientSession() as session:
                response = await session.post(
                    "http://45.77.138.231/api/customer", data=create_customer_payload
                )
                json_response = await response.json()
                if json_response["result"] == "success":
                    customer_id = json_response["message"]
                    return customer_id

        customer_id = await create_customer(member)
        if customer_id:
            create_key_payload = {
                "api_token": self.bot.config.extra_tokens.api_token,
                "product_id": self.bot.config.extra_tokens.product_id,
                "validity": "31622400",
                "customer_id": customer_id,
            }
            async with aiohttp.ClientSession() as session:
                response = await session.post(
                    "http://45.77.138.231/api/create", data=create_key_payload
                )
                json_response = await response.json()
                if json_response["result"] == "success":
                    channel = await self.bot.fetch_channel(CHANNEL_LOG_ID)
                    await channel.send(
                        f"Created key {json_response['message']} at "
                        f"{datetime.datetime.now().strftime('%B %d, %Y %I:%M %p')} "
                        f"for {member.name} ({member.id})"
                    )

                try:
                    await member.send(json_response["message"])
                    await ctx.confirm("Key created and sent.")
                except discord.Forbidden:
                    await ctx.send("User has dms off/bot blocked.")

    # events

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if not await self.should_verify(payload.guild_id, payload.message_id):
            return

        guild = self.bot.get_guild(GUILD_ID)
        role = await self.get_config("role")
        # Todo: do something if this is None
        verify_role = guild.get_role(int(role))

        emoji = await self.get_config("emoji")
        if payload.emoji.id != int(emoji):
            return

        member: discord.Member = await guild.fetch_member(payload.user_id)
        await member.add_roles(verify_role, reason="Verification")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if not await self.should_verify(payload.guild_id, payload.message_id):
            return

    async def should_verify(self, guild_id: int, message_id: int) -> bool:
        # wrong guild
        if guild_id != GUILD_ID:
            return False

        # wrong message
        verify_message = await self.get_config("message")
        if not verify_message:
            return False

        verify_message_id = int(verify_message.split("-")[1])
        if verify_message_id != message_id:
            return False

        # Toggle
        status = await self.get_config("status")
        if not status or not int(status):
            return False

        # unset
        if (
            not await self.get_config("message")
            or not await self.get_config("emoji")
            or not await self.get_config("role")
        ):
            return False

        return True

    # database

    @staticmethod
    async def set_config(key: str, value: str) -> None:
        async with db.get_database() as conn:
            await conn.execute(
                'INSERT INTO grubninja_settings (key, "value") VALUES (?, ?) '
                'ON CONFLICT (key) DO UPDATE SET "value" = EXCLUDED.value;',
                (key, value),
            )

            await conn.commit()

    @staticmethod
    async def get_config(key: str) -> Optional[str]:
        async with db.get_database() as conn:
            cursor = await conn.execute(
                'SELECT "value" FROM grubninja_settings WHERE key = (?);', (key,)
            )
            res = await cursor.fetchone()

        if res:
            return res[0]

    @staticmethod
    async def get_all_config() -> Optional[list]:
        async with db.get_database() as conn:
            cursor = await conn.execute("SELECT * FROM grubninja_settings;")
            res = await cursor.fetchall()

        if res:
            return list(res)


def setup(bot: commands.Bot):
    bot.add_cog(Grubninja(bot))
