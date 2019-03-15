#Stolen from a cheese grater
#https://github.com/XuaTheGrate/Adventure/blob/master/cogs/help.py#L45-L72

# -> Pip packages
from discord.ext import commands
import discord

class Help(commands.Cog):
    """Cog to handle the *super awesome* ***HELP COMMAND***."""
    def __init__(self, bot):
        self.bot = bot

    def formatter(self, i, stack=1, ignore_hidden=False):
        for cmd in i:
            if cmd.hidden and not ignore_hidden:
                continue
            yield "\u200b " * (stack*2) + f"►{cmd}\n"
            if isinstance(cmd, commands.Group):
                yield from self.formatter(cmd.commands, stack+1)

    def format_help_for(self, item):
        embed = discord.Embed(colour=discord.Colour.blurple())
        embed.set_footer(text="Use *help <command> for more information.")
        if isinstance(item, commands.Cog):
            embed.title = item.qualified_name
            embed.description = type(item).__doc__
            embed.add_field(name="Commands", value=''.join([t for t in self.formatter(item.get_commands())]))
            return embed
        elif isinstance(item, commands.Group):
            embed.title = item.signature
            embed.description = item.help
            fmt = "".join([c for c in self.formatter(item.commands)])
            embed.add_field(name="Subcommands", value=fmt)
            return embed
        elif isinstance(item, commands.Command):
            embed.title = item.signature
            embed.description = item.help
            return embed
        else:
            raise RuntimeError("??")

    @commands.command(name="help")
    async def _help(self, ctx, *, cmd: commands.clean_content=None):
        """The help command.
        Use this to view other commands."""
        if cmd == "all":
            _all = True
            cmd = None
        else:
            _all = False
        if not cmd:
            embed = discord.Embed(color=discord.Color.blurple())
            embed.set_author(name=f"{ctx.me.display_name}'s Commands.", icon_url=ctx.me.avatar_url_as(format="png",
                                                                                                      size=32))
            embed.set_footer(text=f"Prefix: {ctx.prefix}")
            n = []
            for cog in self.bot.cogs.values():
                if sum(1 for n in cog.get_commands() if not (n.hidden and not _all)) == 0:
                    continue
                n.append(f"**{cog.qualified_name}**\n")
                for cmd in self.formatter(cog.get_commands(), ignore_hidden=_all):
                    n.append(cmd)
            embed.description = "".join(n)
            await ctx.send(embed=embed)
        else:
            item = self.bot.get_cog(cmd) or self.bot.get_command(cmd)
            if not item:
                return await ctx.send(f"Couldn't find any cog/command named '{cmd}'.")
            await ctx.send(embed=self.format_help_for(item))

def setup(bot):
    bot.old_help = bot.remove_command("help")
    bot.add_cog(Help(bot))

def teardown(bot):
    bot.add_command(bot.old_help)
