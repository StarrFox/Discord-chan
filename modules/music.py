import discord
from discord.ext import commands
import asyncio
import wavelink
import re
import humanize

class Status(commands.Cog):

    def __init__(self, bot, guild_id, dj):
        self.bot = bot
        self.guild_id = guild_id
        self.queue = []
        self.current = None
        self.dj = dj #member id

    def is_dj(self, user_id):
        return user_id == self.dj

    async def next(self):
        player = self.bot.wavelink.get_player(self.guild_id)
        if len(self.queue) != 0:
            song = self.queue[0]
            await player.play(song)
            self.queue.remove(song)
            self.current = song

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
            status = await self.get_status(event.player)
            await status.next()

    async def get_status(self, value):
        if isinstance(value, commands.Context):
            guild_id = value.guild.id
            dj = value.author.id
        else:
            guild_id = value.guild_id
            dj = None
        try:
            status = self.statuses[guild_id]
        except KeyError:
            status = Status(self.bot, guild_id, dj)
            self.statuses[guild_id] = status
        return status

    async def join(self, ctx):
        """Joins a vc"""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        await player.connect(ctx.author.voice.channel.id)

    @commands.command()
    async def play(self, ctx, *, entry):
        """Plays a song or adds it to queue"""
        if not ctx.author.voice:
            return await ctx.send("You must be in a vc to use this command")
        if not RURL.match(entry):
            entry = f'ytsearch:{entry}'
            url = False
        else:
            url = True
        tracks = await self.bot.wavelink.get_tracks(entry)
        if not tracks: #No songs found
            return await ctx.send('Nothing found for that entry')
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            await self.join(ctx)
        status = await self.get_status(ctx)
        if isinstance(tracks, wavelink.player.TrackPlaylist):
            tracks = tracks.tracks
        if url:
            for i in tracks:
                status.queue.append(i)
            tmsg = "\n".join([i.title for i in tracks[:5]])
        else:
            status.queue.append(tracks[0])
            tmsg = tracks[0].title
        await ctx.send(f'Added {tmsg} to the queue', delete_after=15)
        if not status.current:
            await status.next()

    @commands.command(aliases=['next'])
    async def skip(self, ctx):
        """Skip the current song"""
        if not ctx.author.voice:
            return await ctx.send("You must be in a vc to use this command")
        status = await self.get_status(ctx)
        if not status.current:
            return await ctx.send("Nothing to skip")
        if status.is_dj(ctx.author.id) or ctx.author.guild_permissions.administrator:
            await status.next()
            return await ctx.send("Skipped")
        await ctx.send("You aren't an admin or the dj")

    @commands.command()
    async def pause(self, ctx):
        """Pause the song"""
        if not ctx.author.voice:
            return await ctx.send("You must be in a vc to use this command")
        status = await self.get_status(ctx)
        if not status.is_dj(ctx.author.id) and not ctx.author.guild_permissions.administrator:
            return await ctx.send("You aren't an admin or the dj")
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_playing:
            return await ctx.send('Not playing anything', delete_after=15)
        await ctx.send('Pausing', delete_after=15)
        await player.set_pause(True)

    @commands.command()
    async def resume(self, ctx):
        """Resume the song"""
        if not ctx.author.voice:
            return await ctx.send("You must be in a vc to use this command")
        status = await self.get_status(ctx)
        if not status.is_dj(ctx.author.id) and not ctx.author.guild_permissions.administrator:
            return await ctx.send("You aren't an admin or the dj")
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.paused:
            return await ctx.send("Isn't paused", delete_after=15)
        await ctx.send('Resuming', delete_after=15)
        await player.set_pause(False)

    @commands.command()
    async def volume(self, ctx, num: int):
        """Set the volume"""
        if not ctx.author.voice:
            return await ctx.send("You must be in a vc to use this command")
        if not 0 <= num <= 100:
            return await ctx.send("Volume must be between 0 and 100")
        status = await self.get_status(ctx)
        if not status.is_dj(ctx.author.id) and not ctx.author.guild_permissions.administrator:
            return await ctx.send("You aren't an admin or the dj")
        player = self.bot.wavelink.get_player(ctx.guild.id)
        await player.set_volume(num)
        await ctx.send(f"Volume set to {num}")

    @commands.command(aliases=['leave', 'dc', 'disconnect'])
    async def stop(self, ctx):
        """Stop playing and leave"""
        if not ctx.author.voice:
            return await ctx.send("You must be in a vc to use this command")
        player = self.bot.wavelink.get_player(ctx.guild.id)
        status = await self.get_status(ctx)
        if not status.is_dj(ctx.author.id) and not ctx.author.guild_permissions.administrator:
            return await ctx.send("You aren't an admin or the dj")
        try:
            del self.statuses[ctx.guild.id]
        except KeyError:
            await player.disconnect()
            return await ctx.send('Nothing playing')
        await player.disconnect()
        await ctx.send('Stopped', delete_after=20)

    @commands.group(aliases=['queue', 'np', 'playing'], invoke_without_command=True)
    async def current(self, ctx):
        """Get info on the current song and the next 5 in queue"""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_playing:
            return await ctx.send("Not playing anything")
        status = await self.get_status(ctx)
        nxt5 = "\n".join([i.title for i in status.queue[:5]])
        await ctx.send(f"```Current:\n{status.current}\n\nUpcoming:\n{nxt5}```")

    @current.command()
    async def clear(self, ctx):
        """Clear the queue"""
        if not ctx.author.voice:
            return await ctx.send("You must be in a vc to use this command")
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_playing:
            return await ctx.send("Not playing anything")
        status = await self.get_status(ctx)
        if not status.is_dj(ctx.author.id) and not ctx.author.guild_permissions.administrator:
            return await ctx.send("You aren't an admin or the dj")
        status.queue = []
        await ctx.send("Queue cleared")

    @commands.command()
    async def dj(self, ctx, dj: discord.Member):
        """Swap dj to someone else"""
        status = await self.get_status(ctx)
        if not status.is_dj(ctx.author.id) and not ctx.author.guild_permissions.administrator:
            return await ctx.send("You aren't an admin or the dj")
        status.dj = dj.id
        await ctx.send(f"Made {dj.display_name} the dj")

    @commands.command(aliases=['wl'])
    async def wlinfo(self, ctx):
        """Info about wavelink"""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        node = player.node
        used = humanize.naturalsize(node.stats.memory_used)
        total = humanize.naturalsize(node.stats.memory_allocated)
        free = humanize.naturalsize(node.stats.memory_free)
        dex = f'Version: {wavelink.__version__}\n' \
              f'Nodes: {len(self.bot.wavelink.nodes)}\n' \
              f'Players: {len(self.bot.wavelink.players)}'
        e = discord.Embed(
            title = "Wavelink stats",
            color = discord.Color.blurple(),
            description = dex
        )
        e.add_field(
            name = "Memory",
            value = f"Used: {used}\nTotal: {total}\nFree: {free}"
        )
        await ctx.send(embed=e)

def setup(bot):
    bot.add_cog(music(bot))