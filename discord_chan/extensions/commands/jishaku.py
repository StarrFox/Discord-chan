# -*- coding: utf-8 -*-
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

import discord
from discord.ext import commands
from jishaku.codeblocks import codeblock_converter, Codeblock
from jishaku.cog import jsk
from jishaku.cog_base import JishakuBase
from jishaku.exception_handling import ReplResponseReactor
from jishaku.flags import SCOPE_PREFIX
from jishaku.metacog import GroupCogMeta
from jishaku.paginators import PaginatorInterface
from jishaku.repl import get_var_dict_from_ctx, AsyncCodeExecutor, AsyncSender
from terminaltables import AsciiTable
from aiosqlite import OperationalError

from discord_chan import DCMenuPages, NormalPageSource, PartitionPaginator, SubContext, db

try:
    import psutil
except ImportError:
    psutil = None


class Jishaku(JishakuBase, metaclass=GroupCogMeta, command_parent=jsk):

    @commands.command(name="py", aliases=["python"])
    async def jsk_python(self, ctx: SubContext, *, argument: codeblock_converter):
        arg_dict = get_var_dict_from_ctx(ctx, SCOPE_PREFIX)
        arg_dict["_"] = self.last_result

        scope = self.scope

        try:
            async with ReplResponseReactor(ctx.message):
                with self.submit(ctx):
                    executor = AsyncCodeExecutor(argument.content, scope, arg_dict=arg_dict)
                    async for send, result in AsyncSender(executor):
                        if result is None:
                            continue

                        self.last_result = result

                        if isinstance(result, discord.File):
                            send(await ctx.send(file=result))
                        elif isinstance(result, discord.Embed):
                            send(await ctx.send(embed=result))
                        elif isinstance(result, PaginatorInterface):
                            send(await result.send_to(ctx))
                        elif isinstance(result, DCMenuPages):
                            send(await result.start(ctx))
                        else:
                            if not isinstance(result, str):
                                # repr all non-strings
                                result = repr(result)

                            result = result.replace(self.bot.http.token, '[token omitted]')
                            if result.strip() == '':
                                result = '[empty string]'

                            if len(result) > 2000:
                                paginator = PartitionPaginator(prefix='```py')

                                paginator.add_line(result)

                                source = NormalPageSource(paginator.pages)

                                menu = DCMenuPages(source)

                                send(await menu.start(ctx))

                            else:
                                send(await ctx.send(f'```py\n{result}```', no_edit=True))

        finally:
            scope.clear_intersection(arg_dict)

    @commands.command(name='pip')
    async def jsk_pip(self, ctx: commands.Context, *, argument: codeblock_converter):
        """
        Shortcut for 'jsk sh pip'. Invokes the system shell.
        """
        return await ctx.invoke(self.jsk_shell, argument=Codeblock(argument.language, 'pip ' + argument.content))

    @commands.command(name='db', aliases=['sql'])
    async def jsk_db(self, ctx: commands.Context, *, quarry: str):
        """
        Execute a db quarry
        """
        async with db.get_database() as connection:
            try:
                cursor = await connection.execute(quarry)
            except OperationalError as e:
                return await ctx.send(str(e))

            await connection.commit()
            quarry_result = await cursor.fetchall()

            if quarry_result:
                collums = [coll[0] for coll in cursor.description]
                final = [collums]

                for data in quarry_result:
                    final.append(list(data))

                table = AsciiTable(final)

                paginator = PartitionPaginator(prefix='```sql', max_size=1000, wrap_on=('|', '\n'))

                paginator.add_line(table.table)

                source = NormalPageSource(paginator.pages)

                menu = DCMenuPages(source)

                await menu.start(ctx)

            else:
                await ctx.send('[no result]')

def setup(bot: commands.Bot):
    bot.add_cog(Jishaku(bot=bot))