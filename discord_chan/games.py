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
from random import choice, randint, shuffle
from typing import Optional, Tuple, Union

import discord
import numpy
from discord.ext import menus


class Connect4(menus.Menu):
    filler = "\N{BLACK LARGE SQUARE}"
    red = "\N{LARGE RED CIRCLE}"
    blue = "\N{LARGE BLUE CIRCLE}"
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
        self.board = numpy.full((6, 7), self.filler)
        # This is kinda hacky but /shrug
        for button in [
            menus.Button(num, self.do_number_button) for num in self.numbers
        ]:
            self.add_button(button)

    def reaction_check(self, payload):
        if payload.message_id != self.message.id:
            return False

        if payload.user_id != self.current_player.id:
            return False

        return payload.emoji in self.buttons

    async def send_initial_message(self, ctx, channel):
        return await channel.send(self.discord_message)

    async def do_number_button(self, payload):
        move_column = self.numbers.index(payload.emoji.name)
        move_row = self.free(move_column)

        # self.free returns None if the column was full
        if move_row is not None:
            self.make_move(move_row, move_column)

            # timeouts count as wins
            self.winner = self.current_player

            if self.check_wins():
                self.winner = self.current_player
                self.stop()

            # Tie
            if self.filler not in self.board:
                self.winner = self.players
                self.stop()

            self.current_player = next(self.player_cycle)
            await self.message.edit(
                content=self.discord_message, allowed_mentions=self.bot.allowed_mentions
            )

    @menus.button("\N{BLACK DOWN-POINTING DOUBLE TRIANGLE}", position=menus.Last())
    async def do_resend(self, _):
        await self.message.delete()
        self.message = msg = await self.send_initial_message(self.ctx, self.ctx.channel)
        for emoji in self.buttons:
            await msg.add_reaction(emoji)

    @menus.button("\N{CROSS MARK}", position=menus.Last(1))
    async def do_cancel(self, _):
        self.stop()

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
        msg = "\n".join(["".join(i) for i in self.board])
        msg += "\n"
        msg += "".join(self.numbers)
        return msg

    # @property
    # def embed(self):
    #     """
    #     The embed to send to discord
    #     """
    #     board_embed = discord.Embed(description=self.board_message)
    #
    #     if self.last_move is not None:
    #         board_embed.add_field(name="Last move", value=self.last_move, inline=False)
    #
    #     if self._running:
    #         board_embed.add_field(
    #             name="Current turn", value=self.current_player.mention
    #         )
    #
    #     return board_embed

    @property
    def discord_message(self):
        final = ""

        if self.last_move is not None:
            final += "Last move:\n"
            final += self.last_move
            final += "\n"

        if self._running:
            final += "Current turn:\n"
            final += self.current_piece + self.current_player.mention
            final += "\n"

        final += self.board_message

        return final

    def free(self, num: int):
        for i in range(5, -1, -1):
            if self.board[i][num] == self.filler:
                return i

    def make_move(self, row: int, column: int):
        self.board[row][column] = self.current_piece
        self.last_move = (
            f"{self.current_piece}{self.current_player.mention} ({column + 1})"
        )

    def check_wins(self):
        def check(array: list):
            array = list(array)
            for i in range(len(array) - 3):
                if array[i : i + 4].count(self.current_piece) == 4:
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

        for diagonal in [
            *get_diagonals(self.board),
            *get_diagonals(numpy.fliplr(self.board)),
        ]:
            if check(diagonal):
                return True

    async def run(self, ctx) -> Optional[Union[discord.Member, Tuple[discord.Member]]]:
        """
        Run the game and return the winner(s)
        returns None if the first player never made a move
        """
        await self.start(ctx, wait=True)
        return self.winner


class MasterMindMenu(menus.Menu):
    VARIATION_SELECTOR = "\N{VARIATION SELECTOR-16}"

    EMOJI_LIST = [
        "<:wut:595570319490809857>",
        "<:weebagree:665491422295752705>",
        "<:teeth:586043416110956574>",
        "<:teehee:597962329031704587>",
        "<:senpai:582035624899379201>",
    ]

    RESEND_ARROW = "\N{BLACK DOWN-POINTING DOUBLE TRIANGLE}"
    LEFT_ARROW = "\N{BLACK LEFT-POINTING TRIANGLE}" + VARIATION_SELECTOR
    RETURN_ARROW = "\N{LEFTWARDS ARROW WITH HOOK}" + VARIATION_SELECTOR
    # these two don't work with names on lower python versions
    YELLOW_CIRCLE = "\U0001f7e1"
    GREEN_CIRCLE = "\U0001f7e2"
    CROSS_MARK = "\N{CROSS MARK}"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tries = 10
        self.value = None
        self.position = 0
        self.entry = ["X"] * 5
        self.previous_tries = []
        self.code = self.get_code()

        for button in [menus.Button(e, self.do_entry_button) for e in self.EMOJI_LIST]:
            self.add_button(button)

    async def send_initial_message(self, ctx, channel):
        return await ctx.send(
            f"\n{self.YELLOW_CIRCLE} means the emoji is used in the code but in a different position."
            f"\n{self.GREEN_CIRCLE} means the emoji is correct and in the correct position."
            f"\n**Circles are not ordered.**"
            f"\nCode is 5 emojis."
            f"\n\nControls:"
            f"\n<emoji> enter that emoji in the entry box."
            f"\n{self.RESEND_ARROW} resend message interface."
            f"\n{self.LEFT_ARROW} backspace last emoji in entry box."
            f"\n{self.RETURN_ARROW} enters guess.",
        )

    @property
    def console(self) -> str:
        res = [
            f"Tries left: {self.tries}",
            "**Note: Circles are not ordered.**",
            *self.previous_tries,
            " ".join(self.entry),
        ]
        return "\n".join(res)

    async def do_entry_button(self, payload):
        if self.position == 5:
            return await self.ctx.send(
                f"{self.ctx.author.mention}, Max entry reached.", delete_after=5,
            )

        if str(payload.emoji) in self.entry:
            return await self.ctx.send(
                f"{self.ctx.author.mention}, No duplicate emojis.", delete_after=5,
            )

        self.entry[self.position] = str(payload.emoji)
        self.position += 1
        await self.message.edit(content=self.console)

    @menus.button(RESEND_ARROW, position=menus.Last())
    async def do_resend(self, _):
        await self.message.delete()
        self.message = msg = await self.ctx.send(self.console)
        for emoji in self.buttons:
            await msg.add_reaction(emoji)

    @menus.button(LEFT_ARROW, position=menus.Last(1))
    async def do_backspace(self, _):
        if self.position == 0:
            return

        self.position -= 1
        self.entry[self.position] = "X"
        await self.message.edit(content=self.console)

    @menus.button(RETURN_ARROW, position=menus.Last(2))
    async def do_enter(self, _):
        if self.position != 5:
            return await self.ctx.send(
                f"{self.ctx.author.mention}, Entry not full.", delete_after=5,
            )

        if self.entry == self.code:
            self.value = 100 * self.tries
            self.stop()
            return

        dots = self.get_dots()
        self.previous_tries.append(f"{' '.join(self.entry)} => {dots}")

        self.entry = ["X"] * 5
        self.position = 0
        self.tries -= 1

        await self.message.edit(content=self.console)

        if self.tries == 0:
            self.value = 0

            await self.ctx.send(
                f'Sorry {self.ctx.author.mention}, out of tries. The code was\n{" ".join(self.code)}.',
            )

            self.stop()

    async def run(self, ctx) -> Optional[int]:
        await self.start(ctx, wait=True)
        return self.value

    def get_code(self):
        copy_emojis = self.EMOJI_LIST.copy()
        shuffle(copy_emojis)
        return copy_emojis

    def get_dots(self):
        res = []
        for guess, correct in zip(self.entry, self.code):
            if guess == correct:
                res.append(self.GREEN_CIRCLE)

            elif guess in self.code:
                res.append(self.YELLOW_CIRCLE)

        if not res:
            return self.CROSS_MARK

        return "".join(sorted(res))


class SliderGame(menus.Menu):
    SPACER = "\N{BLACK LARGE SQUARE}"
    SLIDER_EMOJIS = [
        "<:dc_0:725302403712155678>",
        "<:dc_1:725302408472952892>",
        "<:dc_2:725302422854959106>",
        "<:dc_3:725302426999062618>",
        "<:dc_4:725302430966743042>",
        "<:dc_5:725302444388515950>",
        "<:dc_6:725302448633151559>",
        "<:dc_7:725302452768866336>",
        "<:dc_8:725302465150582795>",
        "<:dc_9:725302469592350791>",
        "<:dc_10:725302474067410995>",
        "<:dc_11:725302486990061628>",
        "<:dc_12:725302491578630235>",
        "<:dc_13:725302496452673587>",
        "<:dc_14:725302508154650688>",
        SPACER,
    ]

    RESEND_ARROW = "\N{BLACK DOWN-POINTING DOUBLE TRIANGLE}"
    CROSS_MARK = "\N{CROSS MARK}"

    ARROW_LEFT = "\N{BLACK LEFT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}"
    ARROW_RIGHT = "\N{BLACK RIGHT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}"
    ARROW_UP = "\N{UP-POINTING SMALL RED TRIANGLE}"
    ARROW_DOWN = "\N{DOWN-POINTING SMALL RED TRIANGLE}"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.board = self.get_board()
        self.positon = self._find_spacer()
        self._randomize_board()

        self.moves = 0
        self.has_won = False

        for button in [
            menus.Button(e, self.do_arrow_move)
            for e in [self.ARROW_LEFT, self.ARROW_DOWN, self.ARROW_UP, self.ARROW_RIGHT]
        ]:
            self.add_button(button)

    async def send_initial_message(self, ctx, channel):
        return await channel.send(self.discord_message)

    async def check_wins(self):
        to_check = []
        for row in self.board:
            for emoji in row:
                to_check.append(emoji)

        if to_check == self.SLIDER_EMOJIS:
            self.has_won = True
            self.stop()

    def _randomize_board(self):
        for _ in range(randint(100, 200)):
            self.random_move()

    # It's pronounced "big brain" :sunglasses:
    def _find_spacer(self):
        for row_index, row in enumerate(self.board):
            for emoji_index, emoji in enumerate(row):
                if emoji == self.SPACER:
                    return row_index, emoji_index

    @property
    def discord_message(self):
        msg = ""
        for row in self.board:
            msg += "".join(row)
            msg += "\n"

        return msg

    def get_board(self):
        emojis = self.SLIDER_EMOJIS.copy()
        board = [*self._groups_of_four(emojis)]

        return board

    @staticmethod
    def _groups_of_four(ungrouped):
        for i in range(0, len(ungrouped), 4):
            try:
                yield ungrouped[i : i + 4]
            except IndexError:
                yield ungrouped[i : i + 3]

    @menus.button(RESEND_ARROW, position=menus.Last())
    async def do_resend(self, _):
        await self.message.delete()
        self.message = msg = await self.ctx.send(self.discord_message)
        for emoji in self.buttons:
            await msg.add_reaction(emoji)

    @menus.button(CROSS_MARK, position=menus.Last(1))
    async def do_forfeit(self, _):
        self.stop()

    async def do_arrow_move(self, payload: discord.RawReactionActionEvent):
        emoji = str(payload.emoji)

        # switch statement be like: bruh?
        if emoji == self.ARROW_LEFT:
            new_position = self.left
        elif emoji == self.ARROW_RIGHT:
            new_position = self.right
        elif emoji == self.ARROW_DOWN:
            new_position = self.down
        elif emoji == self.ARROW_UP:
            new_position = self.up
        else:
            new_position = None

        if not 0 <= new_position[0] <= 3 or not 0 <= new_position[1] <= 3:
            return await self.ctx.send(
                f"{self.ctx.author.mention}, that move is invalid.",
                allowed_mentions=discord.AllowedMentions(users=True),
                delete_after=5,
            )

        self.move(new_position)

        self.moves += 1

        await self.message.edit(content=self.discord_message)
        await self.check_wins()

    @property
    def up(self):
        return self.positon[0] - 1, self.positon[1]

    @property
    def down(self):
        return self.positon[0] + 1, self.positon[1]

    @property
    def right(self):
        return self.positon[0], self.positon[1] + 1

    @property
    def left(self):
        return self.positon[0], self.positon[1] - 1

    def move(self, new_position: Tuple[int, int]):
        emoji = self.board[new_position[0]][new_position[1]]

        self.board[new_position[0]][new_position[1]] = self.SPACER
        self.board[self.positon[0]][self.positon[1]] = emoji
        self.positon = new_position

    def random_move(self):
        new_position = choice([self.up, self.down, self.right, self.left])
        if not 0 <= new_position[0] <= 3 or not 0 <= new_position[1] <= 3:
            return

        self.move(new_position)

    async def run(self, ctx):
        await self.start(ctx, wait=True)
        return self.has_won, self.moves
