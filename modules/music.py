import discord
from discord.ext import commands
import asyncio
import wavelink
import re

class status:

    def __init__(self, bot, guild_id):
        self.bot = bot
        self.guild_id = guild_id
        self.queue = []

    async def next(self):
        player = self.bot.wavelink.get_player(self.guild_id)
        if len(self.queue) != 0:
            song = self.queue[0]
            await player.play(song)
            self.queue.remove(song)

RURL = re.compile('https?:\/\/(?:www\.)?.+')

class music:

    def __init__(self, bot):
        self.bot = bot
        self.statuses = {} #{guild_id: status}
        self.bot.wavelink = wavelink.Client(self.bot)
        self.bot.loop.create_task(self.start_nodes())

    async def start_nodes(self):
        await self.bot.wait_until_ready()
        node = await self.bot.wavelink.initiate_node(host='0.0.0.0',
                                                     port=2333,
                                                     rest_uri='http://0.0.0.0:2333',
                                                     password=self.bot.settings['wavelink_pass'],
                                                     identifier='Bot',
                                                     region='us_central')
        node.set_hook(self.on_event_hook)

    async def on_event_hook(self, event):
        if isinstance(event, (wavelink.TrackEnd, wavelink.TrackException)):
            status = self.get_status(event.player)
            await status.next()

    async def get_status(self, value):
        if isinstance(value, commands.Context):
            guild_id = value.guild.id
        else:
            guild_id = value.guild_id
        try:
            status = self.statuses[guild_id]
        except KeyError:
            status = status(self.bot, guild_id)
            self.statuses[guild_id] = status
        return status

    async def join(self, ctx):
        """Joins a vc"""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        await player.connect(ctx.channel.id)

    @commands.command()
    async def play(self, ctx, *, entry):
        """Plays a song or adds it to queue"""
        if not RURL.match(query):
            query = f'ytsearch:{query}'
        tracks = await self.bot.wavelink.get_tracks(query)
        if not tracks: #No songs found
            return await ctx.send('Nothing found for that entry')
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            await self.join(ctx)
        status = self.get_status(ctx)
        if len(status.queue) == 0:
            first_song = True
        status.queue.append(tracks)
        tmsg = ", ".join([i.title for i in tracks])
        await ctx.send(f'Added {tmsg} to the queue', delete_after=15)
        if first_song:
            await status.next()

def setup(bot):
    bot.add_cog(music(bot))