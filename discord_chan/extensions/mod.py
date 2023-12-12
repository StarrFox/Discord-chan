import typing
from contextlib import suppress
from operator import attrgetter

import discord
from discord.ext import commands

import discord_chan
from discord_chan import BetweenConverter, SubContext, EnumConverter


def is_above(invoker: discord.Member, user: discord.Member):
    return invoker.top_role > user.top_role


class PermForFlags(commands.FlagConverter, prefix="--", delimiter=""):
    channel: discord.abc.GuildChannel | None = None


class Mod(commands.Cog, name="mod"):
    """Moderation commands"""

    def __init__(self, bot: discord_chan.DiscordChan):
        self.bot = bot

    @commands.group(aliases=["feature"], invoke_without_command=True)
    @commands.guild_only()
    async def features(self, ctx: SubContext):
        """
        Get current feature status
        """
        enabled, disabled = await self.bot.feature_manager.get_status(ctx.guild.id)
        await ctx.send(
            f"enabled: {', '.join(map(attrgetter('name'), enabled))}"
            f"\ndisabled: {', '.join(map(attrgetter('name'), disabled))}"
        )

    @features.command(name="toggle")
    @discord_chan.checks.guild_owner()
    async def features_toggle(
        self,
        ctx: SubContext,
        feature: typing.Annotated[
            discord_chan.Feature, EnumConverter(discord_chan.Feature)
        ],
    ):
        """
        Toggle a feature
        """
        enabled = await self.bot.feature_manager.toggle(feature, ctx.guild.id)

        if enabled:
            return await ctx.confirm(f"{feature} enabled")
        else:
            return await ctx.confirm(f"{feature} disabled")

    # this one is has_permissions because channel overrides should be allowed
    @commands.command()
    @commands.bot_has_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge(
        self,
        ctx: SubContext,
        number: typing.Annotated[int, BetweenConverter(0, 1000)],
        user: discord.Member | None = None,
        *,
        text: str | None = None,
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
        try:
            await ctx.guild.fetch_member(member_id)
        except (discord.Forbidden, discord.HTTPException):
            await ctx.guild.ban(discord.Object(id=member_id), reason=reason)
            return await ctx.confirm("Id hackbanned")

        await ctx.send("Member is currently in this guild")

    @commands.group(
        invoke_without_command=True, aliases=["permission", "perms", "perm"]
    )
    @commands.guild_only()
    async def permissions(self, ctx: SubContext):
        """
        Base command for permission commands
        """
        await ctx.send_help("perm")

    @staticmethod
    def get_perm_diff(
        default_perms: discord.Permissions, role_perms: discord.Permissions
    ) -> list[str]:
        default_role_permissions = dict(default_perms)

        differences = []
        for permission_name, value in role_perms:
            if value is True and default_role_permissions[permission_name] is False:
                differences.append(permission_name)

        return differences

    def get_perm_overwrite_messages(
        self, overwrites: discord.PermissionOverwrite
    ) -> tuple[str | None, str | None]:
        allowed: list[str] = []
        denied: list[str] = []

        # True = allowed, False = denied, None = unchanged
        for name, value in overwrites:
            if value is True:
                allowed.append(name)
            elif value is False:
                denied.append(name)

        allowed_message = self.format_perm_names(allowed) if allowed else None
        denied_message = self.format_perm_names(denied) if denied else None

        return allowed_message, denied_message

    @staticmethod
    def format_perm_names(perm_names: list[str]) -> str:
        return ", ".join(map(lambda perm: "`" + perm + "`", perm_names))

    @permissions.command(name="for")
    async def permissions_for(
        self,
        ctx: SubContext,
        target: discord.Member | discord.Role,
        *,
        flags: PermForFlags,
    ):
        """
        Get permissions for a user or role
        """
        default_perms = ctx.guild.default_role.permissions

        if isinstance(target, discord.Role):
            target_perms = target.permissions
        else:
            target_perms = target.guild_permissions

        if differences := self.get_perm_diff(default_perms, target_perms):
            difference_message = self.format_perm_names(differences)

            singular = "s" if len(differences) > 1 else ""

            message = (
                f"{target.mention}'s extra permission{singular}: {difference_message}"
            )
        else:
            message = f"{target.mention} has no extra permissions beyond the default"

        if flags.channel is not None:
            overwrites = flags.channel.overwrites_for(target)
            allowed, denied = self.get_perm_overwrite_messages(overwrites)

            if allowed is not None or denied is not None:
                message += f"\n\nOverwrites in {flags.channel.mention}:\n"
                if allowed is not None:
                    message += f"- Allowed: {allowed}\n"
                if denied is not None:
                    message += f"- Denied: {denied}\n"

        return await ctx.send(message)

    @permissions.command(name="roles")
    async def role_permissions_list(self, ctx: SubContext):
        """
        List all role permissions
        """
        normal_role_parts: list[str] = []
        managed_role_parts: list[str] = []

        for role in ctx.guild.roles:
            if role != ctx.guild.default_role:
                differences = self.get_perm_diff(
                    ctx.guild.default_role.permissions, role.permissions
                )
                if differences:
                    difference_message = self.format_perm_names(differences)

                    role_message = f"{role.mention}: " + difference_message

                    if role.managed:
                        managed_role_parts.append(role_message)
                    else:
                        normal_role_parts.append(role_message)

        if normal_role_parts or managed_role_parts:
            message = ""

            if normal_role_parts:
                message += "\n".join(reversed(normal_role_parts))

            if managed_role_parts:
                singular = "s" if len(managed_role_parts) > 1 else ""

                message += f"\n\nManaged role{singular}:\n"
                message += "\n".join(reversed(managed_role_parts))

        else:
            message = "No roles enable extra permissions"

        return await ctx.send(message)


async def setup(bot):
    await bot.add_cog(Mod(bot))
