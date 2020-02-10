# -*- coding: utf-8 -*-
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

from itertools import cycle
from typing import Optional

import discord
import numpy
from discord.ext import menus


class Connect4(menus.Menu):
    filler = '\N{BLACK LARGE SQUARE}'
    red = '\N{LARGE RED CIRCLE}'
    blue = '\N{LARGE BLUE CIRCLE}'
    numbers = [str(i) + "\N{VARIATION SELECTOR-16}\u20e3" for i in range(1, 8)]

    def __init__(self, player1: discord.Member, player2: discord.Member, **kwargs):
        super().__init__(**kwargs)
        self.players = (player1, player2)
        self._player_ids = {p.id for p in self.players}
        self.player_cycle = cycle(self.players)
        self.current_player = next(self.player_cycle)
        self.last_move = None
        self.winner = None
        # noinspection PyTypeChecker
        self.board = numpy.full(
            (6, 7),
            self.filler
        )
        # This is kinda hacky but /shrug
        for button in [menus.Button(num, self.do_number_button) for num in self.numbers]:
            self.add_button(button)

    def reaction_check(self, payload):
        if payload.message_id != self.message.id:
            return False

        if payload.user_id != self.current_player.id:
            return False

        return payload.emoji in self.buttons

    async def send_initial_message(self, ctx, channel):
        return await channel.send(embed=self.embed)

    async def do_number_button(self, payload):
        move_column = self.numbers.index(payload.emoji.name)
        move_row = self.free(move_column)

        # self.free returns None if the column was full
        if move_row is not None:
            self.make_move(move_row, move_column)

            # timeouts count as wins
            self.winner = self.current_player
            self.current_player = next(self.player_cycle)
            await self.message.edit(embed=self.embed)

            if self.check_wins():
                self.winner = self.current_player
                self._running = False
                return

    @menus.button("\N{BLACK DOWN-POINTING DOUBLE TRIANGLE}", position=menus.Last())
    async def do_resend(self, _):
        await self.message.delete()
        self.message = msg = await self.send_initial_message(self.ctx, self.ctx.channel)
        for emoji in self.buttons:
            await msg.add_reaction(emoji)

    @property
    def current_piece(self):
        if self.current_player == self.players[0]:
            return self.red
        else:
            return self.blue

    @property
    def board_message(self):
        """
        The string representing the board for discord
        """
        msg = '\n'.join([''.join(i) for i in self.board])
        msg += '\n'
        msg += ''.join(self.numbers)
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

        if self._running:
            board_embed.add_field(name='Current turn', value=self.current_player.mention)

        return board_embed

    def free(self, num: int):
        for i in range(5, -1, -1):
            if self.board[i][num] == self.filler:
                return i

    def make_move(self, row: int, column: int):
        self.board[row][column] = self.current_piece
        self.last_move = f"{self.current_player.mention}: {column + 1}"

    def check_wins(self):
        def check(array: list):
            array = list(array)
            for i in range(len(array) - 3):
                if array[i:i + 4].count(self.current_piece) == 4:
                    return True

        for row in self.board:
            if check(row):
                return True

        for column in self.board.T:
            if check(column):
                return True

        def get_diagonals(matrix: numpy.ndarray):
            dias = []
            for offset in range(-2, 4):
                dias.append(list(matrix.diagonal(offset)))
            return dias

        for diagonal in [get_diagonals(self.board), get_diagonals(self.board.T)]:
            if check(diagonal):
                return True

    async def run(self, ctx) -> Optional[discord.Member]:
        """
        Run the game and return the winner
        returns None if the first player never made a move
        """
        await self.start(ctx, wait=True)
        return self.winner
