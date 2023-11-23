from discord.ext import commands

from discord_chan import DiscordChan, SubContext


class Todo(commands.Cog, name="todo"):
    def __init__(self, bot: DiscordChan):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def todo(self, ctx: SubContext):
        """
        dc/todo 1m do thing
        """
        pass

    @todo.command(name="repeat")
    async def todo_repeat(self, ctx: SubContext, repeat: int): ...


async def setup(bot):
    await bot.add_cog(Todo(bot))
