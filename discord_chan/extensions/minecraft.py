import aexaroton.server
from discord.ext import commands

import aexaroton
from loguru import logger

import discord_chan


# temporary until I add a thing to set this
glorp_server_id = "j0KYqbV48uhsoKZi"


class Minecraft(commands.Cog):
    def __init__(self, bot: discord_chan.DiscordChan, exaroton_token: str) -> None:
        super().__init__()
        self.bot = bot

        self.exaroton = aexaroton.Client(exaroton_token)

    async def get_guild_default_server(self, server_id: int) -> aexaroton.server.Server:
        if server_id == 1330327277589758076:
            return await self.exaroton.get_server(glorp_server_id)
        
        raise NotImplementedError("other servers not yet supported")

    @commands.group(invoke_without_command=True, aliases=["mc"])
    @discord_chan.checks.some_guilds(1330327277589758076)  # glorp server only for testing
    async def minecraft(self, ctx: discord_chan.SubContext):
        """
        Base minecraft command
        """
        await ctx.send_help("mc")

    @minecraft.command()
    async def me(self, ctx: discord_chan.SubContext, username: str):
        """
        Set your minecraft username
        """
        maybe_username = await self.bot.database.get_minecraft_username(ctx.author.id)

        server = await self.get_guild_default_server(ctx.guild.id)

        if maybe_username is not None:
            await ctx.send(f"Updating previous username ({maybe_username}) to new username ({username})")
            await server.remove_from_player_list("whitelist", [maybe_username])

        await self.bot.database.update_minecraft_username(
            user_id=ctx.author.id, username=username
        )

        await server.add_to_player_list("whitelist", [username])

        await ctx.confirm("Username updated")

    # TODO: allow passing in the name of a server here
    @minecraft.group(invoke_without_command=True)
    async def server(self, ctx: discord_chan.SubContext):
        """
        Control minecraft servers
        """
        server = await self.get_guild_default_server(ctx.guild.id)
        data = server.data

        software = f"{data.software.name} ({data.software.version})" if data.software is not None else "[no software]"
        players = f"({data.players.count}) [{','.join(data.players.list[:5])}]"

        message_parts: list[str] = [
            f"name: {data.name}",
            f"status: {data.status.name}",
            f"address: {data.address}",
            f"software: {software}",
            f"players: {players}"
        ]

        await ctx.send("\n".join(message_parts))
    
    @server.group(name="whitelist", aliases=["wl"], invoke_without_command=True)
    async def server_whitelist(self, ctx: discord_chan.SubContext):
        """
        View server whitelist
        """
        server = await self.get_guild_default_server(ctx.guild.id)

        whitelist_usernames = await server.get_player_list("whitelist")

        if len(whitelist_usernames) == 0:
            return await ctx.send("No one on whitelist")

        usernames = await self.bot.database.get_minecraft_usernames()

        member_message_parts: list[str] = []

        for whitelist_username in whitelist_usernames:
            for user_id, username in usernames.items():
                if whitelist_username == username:
                    if (member := ctx.guild.get_member(user_id)) is not None:
                        member_message_parts.append(f"{whitelist_username}: [{member.mention}]")
                        break
                    else:
                        member_message_parts.append(f"{whitelist_username}: [member not in server ({user_id})]")
                        break
            else:
                member_message_parts.append(whitelist_username)

        await ctx.send("\n".join(member_message_parts))

    @server_whitelist.command(name="sync")
    async def server_whitelist_sync(self, ctx: discord_chan.SubContext):
        """
        Sync whitelist with stored usernames
        """
        server = await self.get_guild_default_server(ctx.guild.id)

        usernames = await self.bot.database.get_minecraft_usernames()
        current = await server.get_player_list("whitelist")

        to_add = list(usernames.values())

        to_remove: list[str] = []
        for name in current:
            if name not in to_add:
                to_remove.append(name)
        
        await server.remove_from_player_list("whitelist", to_remove)
        await server.add_to_player_list("whitelist", to_add)

        await ctx.confirm("Synced")



async def setup(bot: discord_chan.DiscordChan):
    if bot.exaroton_token is not None:
        await bot.add_cog(Minecraft(bot, bot.exaroton_token))
    else:
        logger.info("Exaroton token not set, not loading minecraft module")
