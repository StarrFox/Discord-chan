from discord.ext import commands
import discord

c4_diagonal_data = [
    [(3,0),(2,1),(1,2),(0,3)],
    [(4,0),(3,1),(2,2),(1,3)],
    [(3,1),(2,2),(1,3),(0,4)],
    [(5,0),(4,1),(3,2),(2,3)],
    [(4,1),(3,2),(2,3),(1,4)],
    [(3,2),(2,3),(1,4),(0,5)],
    [(5,1),(4,2),(3,3),(2,4)],
    [(4,2),(3,3),(2,4),(1,5)],
    [(3,3),(2,4),(1,5),(0,6)],
    [(5,2),(4,3),(3,4),(2,5)],
    [(4,3),(3,4),(2,5),(1,6)],
    [(5,3),(4,4),(3,5),(2,6)],
    [(3,6),(2,5),(1,4),(0,3)],
    [(4,6),(3,5),(2,4),(1,3)],
    [(3,5),(2,4),(1,3),(0,2)],
    [(5,6),(4,5),(3,4),(2,3)],
    [(4,5),(3,4),(2,3),(1,2)],
    [(3,4),(2,3),(1,2),(0,1)],
    [(5,5),(4,4),(3,3),(2,2)],
    [(4,4),(3,3),(2,2),(1,1)],
    [(3,3),(2,2),(1,1),(0,0)],
    [(5,4),(4,3),(3,2),(2,1)],
    [(4,3),(3,2),(2,1),(1,0)],
    [(5,3),(4,2),(3,1),(2,0)]
]

class connect4():

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
        self.last_play = None

    def phrase_board(self):
        return "\n".join(map(''.join, self.board)) + "\n" + ''.join(self.emojis)

    def create_board(self):
        return [[self.filler] * 7 for _ in range(6)]

    def make_embed(self):
        embed = discord.Embed(
            description = self.phrase_board()
        )
        embed.add_field(name="Players:", value=f"{self.red}: {self.player_one.mention}\n{self.blue}: {self.player_two.mention}")
        if not self.is_first_run:
            embed.add_field(name="Last move:", value=f"{self.current_player.mention}: {self.last_play+1}", inline=False)
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
        await self.message.add_reaction("\N{BLACK DOWN-POINTING DOUBLE TRIANGLE}")

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
        self.is_first_run = False
        self.last_play = num
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
        diagonals = []
        for c4_d in c4_diagonal_data:
            diagonals.append([self.board[i[0]][i[1]] for i in c4_d])
        for d in diagonals:
            if check_slice(d):
                self.is_running = False
                return

    async def do_game(self):
        self.message = await self.ctx.send(embed=self.make_embed())
        await self.add_reactions()
        while self.is_running:
            try:
                reaction, user = await self.ctx.bot.wait_for(
                    "reaction_add",
                    check=lambda r, u: r.message.id == self.message.id and u == self.current_player and str(r) in self.emojis + ["\N{BLACK DOWN-POINTING DOUBLE TRIANGLE}"],
                    timeout=300
                )
            except:
                await self.message.edit(content="Timed out due to inactivity")
                break
            try:
                await reaction.remove(user)
            except:
                pass
            if str(reaction) == "\N{BLACK DOWN-POINTING DOUBLE TRIANGLE}":
                await self.message.delete()
                self.message = await self.ctx.send(embed=self.make_embed())
                await self.add_reactions()
            else:
                await self.phrase_reaction(str(reaction))
        try:
            await self.message.clear_reactions()
        except:
            pass

class games(commands.Cog):

    @commands.command()
    async def c4(self, ctx, member: discord.Member):
        """
        Play connect4 with another member
        """
        if member == ctx.author or member.bot:
            return await ctx.send("You cannot play against yourself or a bot")
        board = connect4(ctx.author, member, ctx)
        await board.do_game()

def setup(bot):
    bot.add_cog(games())
