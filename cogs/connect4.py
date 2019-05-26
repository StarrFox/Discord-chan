from discord.ext import commands
import discord

class connect_board():
    """
    The actual game
    """

    def __init__(self, p1, p2, ctx):
        self.player_one = p1
        self.player_two = p2
        self.ctx = ctx
        self.red = "\N{LARGE RED CIRCLE}"
        self.blue = "\N{LARGE BLUE CIRCLE}"
        self.filler = "\N{BLACK LARGE SQUARE}"
        self.emojis = [str(i)+"\u20e3" for i in [1,2,3,4,5,6,7]]
        self.board = self.create_board()
        self.is_running = True
        self.message = None
        self.current_player = p1
        self.is_first_run = True

    def phrase_board(self):
        return "\n".join(map(''.join, self.board))+"\n"+''.join(self.emojis)

    def create_board(self):
        return [[self.filler] * 7 for _ in range(6)]

    def make_embed(self):
        embed = discord.Embed(
            description = self.phrase_board()
        )
        embed.add_field(name="Players:", value=f"{self.red}: {self.player_one.mention}\n{self.blue}: {self.player_two.mention}")
        if self.is_running:
            if self.is_first_run:
                embed.add_field(name="Current turn:", value=self.player_one.mention, inline=False)
            elif self.current_player == self.player_one:
                embed.add_field(name="Current turn:", value=self.player_two.mention, inline=False)
            elif self.current_player == self.player_two:
                embed.add_field(name="Current turn:", value=self.player_one.mention, inline=False)
        else:
            embed.add_field(name="Winner:", value=self.current_player.mention, inline=False)
        return embed

    async def add_reactions(self):
        for r in self.emojis:
            await self.message.add_reaction(r)

    async def remove_reactions(self):
        for r in self.emojis:
            await self.message.remove_reaction(r)

    async def find_free(self, num):
        for i in range(6)[::-1]:
            if self.board[i][num] == self.filler:
                return i

    async def phrase_reaction(self, reaction):
        num = self.emojis.index(reaction)
        next = await self.find_free(num)
        if next is None:
            return
        self.board[next][num] = self.red if self.current_player == self.player_one else self.blue
        await self.check_wins()
        await self.message.edit(embed=self.make_embed())
        self.current_player = self.player_two if self.current_player == self.player_one else self.player_one

    async def check_wins(self):
        def check_slice(s):
            if s[0]==s[1]==s[2]==s[3] and s[0] != self.filler:
                return True
            else:
                return False
        for row in self.board:
            for i in range(4):
                if check_slice(row[i:i+4]):
                    self.is_running = False
                    return
        collums = []
        for i in range(7):
            collums.append([self.board[q][i] for q in range(6)])
        for c in collums:
            for i in range(3):
                if check_slice(c[i:i+4]):
                    self.is_running = False
                    return
        diagonal = [
            [
                self.board[3][0], self.board[2][1], self.board[1][2], self.board[0][3]
            ],
            [
                self.board[4][0], self.board[3][1], self.board[2][2], self.board[1][3]
            ],
            [
                self.board[3][1], self.board[2][2], self.board[1][3], self.board[0][4]
            ],
            [
                self.board[5][0], self.board[4][1], self.board[3][2], self.board[2][3]
            ],
            [
                self.board[4][1], self.board[3][2], self.board[2][3], self.board[1][4]
            ],
            [
                self.board[3][2], self.board[2][3], self.board[1][4], self.board[0][5]
            ],
            [
                self.board[5][1], self.board[4][2], self.board[3][3], self.board[2][4]
            ],
            [
                self.board[4][2], self.board[3][3], self.board[2][4], self.board[1][5]
            ],
            [
                self.board[3][3], self.board[2][4], self.board[1][5], self.board[0][6]
            ],
            [
                self.board[5][2], self.board[4][3], self.board[3][4], self.board[2][5]
            ],
            [
                self.board[4][3], self.board[3][4], self.board[2][5], self.board[1][6]
            ],
            [
                self.board[5][3], self.board[4][4], self.board[3][5], self.board[2][6]
            ],
            [
                self.board[3][6], self.board[2][5], self.board[1][4], self.board[0][3]
            ],
            [
                self.board[4][6], self.board[3][5], self.board[2][4], self.board[1][3]
            ],
            [
                self.board[3][5], self.board[2][4], self.board[1][3], self.board[0][2]
            ],
            [
                self.board[5][6], self.board[4][5], self.board[3][4], self.board[2][3]
            ],
            [
                self.board[4][5], self.board[3][4], self.board[2][3], self.board[1][2]
            ],
            [
                self.board[3][4], self.board[2][3], self.board[1][2], self.board[0][1]
            ],
            [
                self.board[5][5], self.board[4][4], self.board[3][3], self.board[2][2]
            ],
            [
                self.board[4][4], self.board[3][3], self.board[2][2], self.board[1][1]
            ],
            [
                self.board[3][3], self.board[2][2], self.board[1][1], self.board[0][0]
            ],
            [
                self.board[5][4], self.board[4][3], self.board[3][2], self.board[2][1]
            ],
            [
                self.board[4][3], self.board[3][2], self.board[2][1], self.board[1][0]
            ],
            [
                self.board[5][3], self.board[4][2], self.board[3][1], self.board[2][0]
            ]
        ]
        for d in diagonal:
            if check_slice(d):
                self.is_running = False
                return

    async def do_game(self):
        self.message = await self.ctx.send(embed=self.make_embed())
        self.is_first_run = False
        await self.add_reactions()
        while self.is_running:
            try:
                reaction, user = await self.ctx.bot.wait_for(
                    "reaction_add",
                    check=lambda r, u: r.message.id == self.message.id and u == self.current_player and str(r) in self.emojis,
                    timeout=300
                )
            except:
                try:
                    await self.remove_reactions()
                except:
                    pass
                await self.message.edit(content="Timed out due to inactivity")
                break
            try:
                await reaction.remove(user)
            except:
                pass
            await self.phrase_reaction(str(reaction))

class connect4(commands.Cog):
    """
    User input
    """

    @commands.command()
    async def c4(self, ctx, target: discord.Member):
        if target == ctx.author or target.bot:
            return await ctx.send("You cannot play against yourself or a bot")
        board = connect_board(ctx.author, target, ctx)
        await board.do_game()

def setup(bot):
    bot.add_cog(connect4())
