import typing
from contextlib import suppress

import discord
from discord.ext import commands

from discord_chan import BetweenConverter, FetchedMember, SubContext


def is_above(invoker: discord.Member, user: discord.Member):
    return invoker.top_role > user.top_role


# class RolePermFlags(commands.FlagConverter, delimiter="", prefix="--"):
#     _list: bool = commands.flag(name="list")


class Mod(commands.Cog, name="mod"):
    """Moderation commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # this one is has_permissions because channel overrides should be allowed
    @commands.command()
    @commands.bot_has_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge(
        self,
        ctx: SubContext,
        number: typing.Annotated[int, BetweenConverter(0, 1000)],
        user: typing.Optional[FetchedMember] = None,
        *,
        text: typing.Optional[str] = None,
    ):
        """
        Purges messages from certain user and/or (with) certain text
        <number> must be between 0 and 1000
        """
        with suppress(discord.Forbidden, discord.NotFound):
            await ctx.message.delete()

        def msgcheck(msg):
            if user and text:
                # Using lower might be inconsistent
                return text in msg.content.lower() and user == msg.author

            elif user:
                return user == msg.author

            elif text:
                return text in msg.content.lower()

            else:
                return True

        # these are the only places the command can be invoked from
        assert isinstance(ctx.channel, discord.abc.Messageable) and isinstance(
            ctx.channel, discord.abc.GuildChannel
        )
        deleted = await ctx.channel.purge(limit=number, check=msgcheck)
        with suppress(discord.Forbidden, discord.NotFound):
            await ctx.send(f"Deleted {len(deleted)} message(s)", delete_after=5)

    @commands.command()
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.has_guild_permissions(ban_members=True)
    @commands.guild_only()
    async def hackban(self, ctx: SubContext, member_id: int, *, reason=None):
        """
        Bans using an id, must not be a current member
        """
        # guild_only ensures this
        assert ctx.guild is not None
        try:
            await ctx.guild.fetch_member(member_id)
        except (discord.Forbidden, discord.HTTPException):
            await ctx.guild.ban(discord.Object(id=member_id), reason=reason)
            return await ctx.confirm("Id hackbanned.")

        await ctx.send("Member is currently in this guild.")

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def role(self, ctx: SubContext):
        """
        Base command for role commands
        """
        await ctx.send_help("role")
    
    # @role.command()
    # @commands.bot_has_guild_permissions(manage_roles=True)
    # @commands.has_guild_permissions(manage_roles=True)
    # async def new(self, ctx: SubContext):
    #     """
    #     Create a new role
    #     """
    #     pass

    @staticmethod
    def get_perm_diff(default_perms: discord.Permissions, role_perms: discord.Permissions) -> list[str]:
        default_role_permissions = dict(default_perms)

        differences = []
        for permission_name, value in role_perms:
            if value is True and default_role_permissions[permission_name] is False:
                differences.append(permission_name)

        return differences

    @role.group(invoke_without_command=True, aliases=["perms", "perm"])
    async def permissions(self, ctx: SubContext, role: discord.Role):
        """
        Manage role permissions
        """
        assert ctx.guild is not None
        differences = self.get_perm_diff(ctx.guild.default_role.permissions, role.permissions)
        difference_message = ", ".join(map(lambda perm: "`" + perm + "`", differences))
        return await ctx.send(f"Enabled permissions: {difference_message}")

    @permissions.command(name="list")
    async def permissions_list(self, ctx: SubContext):
        """
        List all role permissions
        """
        assert ctx.guild is not None

        message_parts: list[str] = []

        for role in ctx.guild.roles:
            if role != ctx.guild.default_role:
                differences = self.get_perm_diff(ctx.guild.default_role.permissions, role.permissions)
                if differences:
                    difference_message = ", ".join(map(lambda perm: "`" + perm + "`", differences))
                    message_parts.append(f"{role.name}: " + difference_message)

        return await ctx.send("\n".join(message_parts))

    # @role.command(name="list")
    # async def _list(self, ctx: SubContext):
    #     """
    #     List current roles
    #     """
    #     pass


async def setup(bot):
    await bot.add_cog(Mod(bot))
