import discord
from discord.ext import commands


class Minimal(commands.MinimalHelpCommand):
    def get_destination(self):
        ctx = self.context
        if self.dm_help is True:
            return ctx.author
        elif self.dm_help is None and len(self.paginator) > self.dm_help_threshold:
            return ctx.author
        else:
            return ctx

    def get_opening_note(self):
        command_name = self.context.invoked_with
        return f"Use `dc/{command_name} <command/cog>` for more info on a command/cog."

    def add_bot_commands_formatting(self, cmds, heading):
        if cmds:
            joined = ", ".join(f"`{c.name}`" for c in cmds)
            self.paginator.add_line(f"**{heading}** - {joined}", empty=False)

    def add_aliases_formatting(self, aliases):
        if not aliases:
            return

        self.paginator.add_line(
            "**{}** {}".format(self.aliases_heading, ", ".join(aliases)), empty=True
        )

    def add_command_formatting(self, command):
        if command.description:
            self.paginator.add_line(command.description, empty=True)

        self.add_aliases_formatting(command.aliases)

        self.paginator.add_line("```", empty=False)

        signature = self.get_command_signature(command)
        if command.aliases:
            self.paginator.add_line(signature, empty=False)
        else:
            self.paginator.add_line(signature, empty=True)

        if command.help:
            try:
                self.paginator.add_line(command.help, empty=True)

            except RuntimeError:
                for line in command.help.splitlines():
                    self.paginator.add_line(line, empty=False)
                    self.paginator.add_line()

        self.paginator.add_line("```")

    async def send_group_help(self, group):
        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)

        self.add_command_formatting(group)

        filtered = await self.filter_commands(group.commands, sort=self.sort_commands)
        if filtered:
            self.paginator.add_line("**%s**:" % self.commands_heading)

            for command in filtered:
                self.add_subcommand_formatting(command)

            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

        await self.send_pages()

    async def send_cog_help(self, cog):
        bot = self.context.bot

        if bot.description:
            self.paginator.add_line(bot.description, empty=True)

        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)

        filtered = await self.filter_commands(
            cog.get_commands(), sort=self.sort_commands
        )
        if filtered:
            self.paginator.add_line(
                f"**{cog.qualified_name} {self.commands_heading.lower()}**"
            )

            for command in filtered:
                self.add_subcommand_formatting(command)

            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

        await self.send_pages()

    # Todo: find better answer
    # I overwrite this to have command > cog rather than the default
    # also to ignore cogs with no commands (see #L142)
    async def command_callback(self, ctx, *, command=None):
        await self.prepare_help_command(ctx, command)
        bot = ctx.bot

        if command is None:
            mapping = self.get_bot_mapping()
            return await self.send_bot_help(mapping)

        maybe_coro = discord.utils.maybe_coroutine

        keys = command.split(" ")
        cmd = bot.all_commands.get(keys[0])

        if cmd is not None:
            if isinstance(cmd, commands.Group):
                for key in keys[1:]:
                    # .all_commands is provided by GroupMixin
                    found = cmd.all_commands.get(key)  # type: ignore

                    if found is None:
                        string = await maybe_coro(
                            self.subcommand_not_found, cmd, self.remove_mentions(key)
                        )
                        return await self.send_error_message(string)

                    cmd = found

            if isinstance(cmd, commands.Group):
                return await self.send_group_help(cmd)
            else:
                return await self.send_command_help(cmd)

        cog = bot.get_cog(command)
        if cog is not None and bool(cog.get_commands()):
            return await self.send_cog_help(cog)

        else:
            string = await maybe_coro(
                self.command_not_found, self.remove_mentions(keys[0])
            )
            return await self.send_error_message(string)
