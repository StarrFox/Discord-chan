from collections.abc import Sequence
import itertools
from typing import Any, Literal, Union
import inspect

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

    def get_opening_note(self) -> str | None:
        return None
        # command_name = self.context.invoked_with
        # return f"Use `dc/{command_name} <command/cog>` for more info on a command/cog."

    def add_bot_commands_formatting(self, cmds: Sequence[commands.Command[Any, ..., Any]], heading: str):
        if cmds:
            joined = ", ".join(c.name for c in cmds)
            self.paginator.add_line(f"{heading}: {joined}", empty=False)

    def add_aliases_formatting(self, aliases: Sequence[str]):
        if not aliases:
            return

        self.paginator.add_line(
            "**{}** {}".format(self.aliases_heading, ", ".join(aliases)), empty=True
        )

    def get_command_signature(self, command: commands.Command[Any, ..., Any]) -> str:
        if command.aliases:
            aliases = "|".join(command.aliases)

            if command.full_parent_name:
                parents = command.full_parent_name + " "
            else:
                parents = ""

            name = f"{parents}[{command.name}|{aliases}]"
        else:
            name = command.qualified_name
        
        return f"{self.context.clean_prefix}{name}"

    def format_command_param(self, param: commands.Parameter, require_var_positional: bool = False) -> str:
        """
        member [Member]=<you> the member to get words of
        words [str...] only show these words if provided
        """
        name = param.displayed_name or param.name

        greedy = isinstance(param.converter, commands.Greedy)
        optional = False  # postpone evaluation of if it's an optional argument

        if param.displayed_default:
            default = f"={param.displayed_default}"
        else:
            default = ""

        if param.description:
            description = " " + param.description
        else:
            description = ""

        annotation: Any = param.converter.converter if greedy else param.converter
        origin = getattr(annotation, '__origin__', None)
        if not greedy and origin is Union:
            none_cls = type(None)
            union_args = annotation.__args__
            optional = union_args[-1] is none_cls
            if len(union_args) == 2 and optional:
                #annotation = union_args[0]
                origin = getattr(annotation, '__origin__', None)

        if annotation is discord.Attachment:
            if optional:
                return f"{name} [Attachment]{default}{description}"
            elif greedy:
                return f"{name} [Attachments...]{default}{description}"
            else:
                return f"{name} <Attachment>{default}{description}"

        if origin is Literal:
            literal_options = '|'.join(f'{v}' if isinstance(v, str) else str(v) for v in annotation.__args__)
            return f"{name} [{literal_options}]{default}{description}"

        try:
            is_flag = issubclass(param.converter, commands.FlagConverter)
        except TypeError:
            is_flag = False

        if not is_flag:
            def _get_converter_name(converter) -> str:
                if inspect.isclass(converter):
                    return converter.__name__
                else:
                    # instance
                    return converter.__class__.__name__

            if origin is Union:
                converter_type = "|".join(
                    _get_converter_name(arg) for arg in annotation.__args__ if arg is not None
                )
            else:
                converter_type = _get_converter_name(annotation)
        else:
            converter_type = "Flags"

        if not param.required:
            if annotation is not None:
                return f"{name} [{converter_type}{'...' if greedy else ''}]{default}{description}"
            else:
                return f"{name}{default}{description}"

        elif param.kind == param.VAR_POSITIONAL:
            if require_var_positional:
                return f"{name} <{converter_type}>{default}{description}"
            else:
                return f"{name} [{converter_type}...]{default}{description}"
        elif greedy:
            return f"{name} [{converter_type}...]{default}{description}"
        elif optional:
            return f"{name} [{converter_type}]{default}{description}"
        else:
            return f"{name} <{converter_type}>{default}{description}"

    def add_command_arguments(self, command: commands.Command[Any, ..., Any]):
        arguments = command.clean_params.values()
        if not arguments:
            return

        self.paginator.add_line(f"Arguments:")

        for argument in arguments:
            formatted_argument = self.format_command_param(
                argument,
                command.require_var_positional
            )

            self.paginator.add_line(formatted_argument)

            try:
                is_flag = issubclass(argument.converter, commands.FlagConverter)
            except TypeError:
                is_flag = False

            if is_flag:
                flags = argument.converter.get_flags()

                for flag_name, flag in flags.items():
                    if flag.description:
                        description = f": {flag.description}"
                    else:
                        description = ""
                    
                    self.paginator.add_line(f"    --{flag_name}{description}")

        self.paginator.add_line()

    def add_command_formatting(self, command: commands.Command[Any, ..., Any], *, in_group: bool = False):
        if not in_group:
            self.paginator.add_line("```")

        if command.description:
            self.paginator.add_line(command.description, empty=True)

        signature = self.get_command_signature(command)
        self.paginator.add_line(signature)

        if command.help:
            self.paginator.add_line()

            try:
                self.paginator.add_line(command.help, empty=True)
            except RuntimeError:
                for line in command.help.splitlines():
                    self.paginator.add_line(line)
                self.paginator.add_line()

        self.add_command_arguments(command)

        if not in_group:
            self.paginator.add_line("```")

    async def send_group_help(self, group: commands.Group[Any, ..., Any]):
        self.paginator.add_line("```")

        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)

        self.add_command_formatting(group, in_group=True)

        filtered = await self.filter_commands(group.commands, sort=self.sort_commands)
        if filtered:
            self.paginator.add_line(f"Subcommands:")

            for command in filtered:
                self.add_subcommand_formatting(command)

            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

        self.paginator.add_line("```")

        await self.send_pages()

    async def send_cog_help(self, cog: commands.Cog):
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

    async def send_bot_help(self, _) -> None:
        ctx = self.context
        bot = ctx.bot

        self.paginator.add_line("```")

        if bot.description:
            self.paginator.add_line(bot.description, empty=True)

        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)

        no_category = f'\u200b{self.no_category}'

        def get_category(command: commands.Command[Any, ..., Any], *, no_category: str = no_category) -> str:
            cog = command.cog
            return cog.qualified_name if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        to_iterate = itertools.groupby(filtered, key=get_category)

        for category, cmds in to_iterate:
            cmds = sorted(cmds, key=lambda c: c.name) if self.sort_commands else list(cmds)
            self.add_bot_commands_formatting(cmds, category)

        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)

        self.paginator.add_line("```")

        await self.send_pages()

    # Todo: find better answer
    # I overwrite this to have command > cog rather than the default
    # also to ignore cogs with no commands (see #L142)
    async def command_callback(self, ctx: commands.Context, *, command: str | None = None):
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
