from discord.ext import commands

class StarrHelp(commands.MinimalHelpCommand):
    """Main help command"""

    def get_opening_note(self):
        command_name = self.context.invoked_with
        return f"Use `{self.clean_prefix}{command_name} <command/cog>` for more info on a command/cog."

    def get_ending_note(self):
        return f"For more help join the support guild via: `{self.clean_prefix}support`"

    def add_bot_commands_formatting(self, commands, heading):
        if commands:
            # U+2002 Middle Dot, space
            joined = ', '.join(f"`{c.name}`" for c in commands)
            self.paginator.add_line(f'**{heading}** - {joined}')

    def add_aliases_formatting(self, aliases):
        if not aliases: return
        self.paginator.add_line('**%s** %s' % (self.aliases_heading, ', '.join(aliases)), empty=True)

    def add_command_formatting(self, command):
        if command.description:
            self.paginator.add_line(command.description, empty=True)
        self.add_aliases_formatting(command.aliases)
        signature = self.get_command_signature(command)
        self.paginator.add_line("```")
        if command.aliases:
            self.paginator.add_line(signature)
        else:
            self.paginator.add_line(signature, empty=True)
        if command.help:
            try:
                self.paginator.add_line(command.help, empty=True)
            except RuntimeError:
                for line in command.help.splitlines():
                    self.paginator.add_line(line)
                    self.paginator.add_line()
        self.paginator.add_line("```")

    async def send_group_help(self, group):
        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)
        self.add_command_formatting(group)
        filtered = await self.filter_commands(group.commands, sort=self.sort_commands)
        if filtered:
            self.paginator.add_line('**%s**:' % self.commands_heading)
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
        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands)
        if filtered:
            self.paginator.add_line('**%s %s**' % (cog.qualified_name, self.commands_heading.lower()))
            for command in filtered:
                self.add_subcommand_formatting(command)

            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)
        await self.send_pages()

def setup(bot):
    bot.help_command = StarrHelp()
