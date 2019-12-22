#  Copyright © 2019 StarrFox
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


from asyncio import TimeoutError
from itertools import cycle

import discord
import numpy
from discord.ext import commands


class Connect4:
    FILLER = '\N{BLACK LARGE SQUARE}'
    RED = '\N{LARGE RED CIRCLE}'
    BLUE = '\N{LARGE BLUE CIRCLE}'
    # Todo: add veriation selector when I have internet again
    NUMBERS = [str(i) + "\N{VARIATION SELECTOR-16}\u20e3" for i in range(1, 8)]
    RESEND = "\N{BLACK DOWN-POINTING DOUBLE TRIANGLE}"

    def __init__(self, ctx: commands.Context, player1: discord.Member, player2: discord.Member):
        self.ctx = ctx
        self.players = (player1, player2)
        self.player_cycle = cycle(self.players)
        self.current_player = next(self.player_cycle)
        self.running = False
        self.message = None
        self.timed_out = False
        self.resend_message = False
        self.last_move = None
        self.board = numpy.full(
            (6, 7),
            self.FILLER
        )

    @property
    def reactions(self):
        return self.NUMBERS + [self.RESEND]

    @property
    def current_piece(self):
        if self.current_player == self.players[0]:
            return self.RED
        else:
            return self.BLUE

    @property
    def board_message(self):
        """
        The string representing the board for discord
        """
        msg = '\n'.join([''.join([i for i in self.board])])
        msg += '\n'
        msg += ''.join(self.NUMBERS)
        return msg

    @property
    def embed(self):
        """
        The embed to send to discord
        """
        board_embed = discord.Embed(
            description=self.board_message
        )

        if self.last_move is not None:
            board_embed.add_field(name='Last move', value=self.last_move, inline=False)

        if self.running:
            board_embed.add_field(name='Current turn', value=self.current_player.mention)

        return board_embed

    def free(self, num: int):
        for i in range(6)[::-1]:
            if self.board[i][num] == self.FILLER:
                return i

    def make_move(self, row: int, collum: int):
        self.board[row][collum] = self.current_piece
        self.last_move = f"{self.current_player.mention}: {collum + 1}"

    def wait_for_check(self, reaction: discord.Reaction, member: discord.Member):
        checks = [
            reaction.message.id == self.message.id,  # messages still dont have an __eq__
            str(reaction) in self.reactions,
            member == self.current_player
        ]
        return all(checks)

    def check_wins(self):
        def check(array: list):
            array = list(array)
            for i in range(len(array) - 3):
                if array[i:i + 4].count(self.current_piece) == 4:
                    return True

        for row in self.board:
            if check(row):
                return True

        for collum in self.board.T:
            if check(collum):
                return True

        def get_diagonals(matrix: numpy.ndarray):
            dias = []
            for offset in range(-2, 4):
                dias.append(matrix.diagonal(offset))
            return dias

        for diagonal in [get_diagonals(self.board), get_diagonals(self.board.T)]:
            if check(diagonal):
                return True

    def phrase_reaction(self, reaction: discord.Reaction):
        if str(reaction) == self.RESEND:
            self.resend_message = True

        else:
            move_collum = self.NUMBERS.index(str(reaction))
            move_row = self.free(move_collum)

            # self.free returns None if the collum was full
            if move_row:
                self.make_move(move_row, move_collum)

                if self.check_wins():
                    self.running = False
                    return

                self.current_player = next(self.player_cycle)

    # This can fail, my command checks if we have the needed perm though
    async def add_reactions(self):
        for reaction in self.reactions:
            await self.message.add_reaction(reaction)

    async def remove_reactions(self):
        try:
            await self.message.clear_reactions()
        except discord.Forbidden:
            for reaction in self.reactions:
                await self.message.remove_reaction(reaction, self.ctx.me)

    async def update(self):
        if self.timed_out:
            content = 'Timed out due to inactivity'
        else:
            content = None

        if self.message is None:
            self.message = await self.ctx.send(content=content, embed=self.embed)

        elif self.resend_message:
            await self.message.delete()
            self.message = await self.ctx.send(content=content, embed=self.embed)
            self.resend_message = False

        else:
            await self.message.edit(content=content, embed=self.embed)

    async def run(self):
        self.running = True
        await self.update()
        await self.add_reactions()
        while self.running:
            await self.update()
            try:
                reaction, _ = await self.ctx.bot.wait_for(
                    'reaction_add',
                    check=self.wait_for_check,
                    timeout=300
                )
            except TimeoutError:
                self.timed_out = True
                self.running = False
            else:
                await self.phrase_reaction(reaction)
        await self.update()
        await self.ctx.send(f'{self.current_player.mention} has won!')
        await self.remove_reactions()
