"""
Based on:
https://gist.github.com/Apfelin/c9cbb7988a9d8e55d77b06473b72dd57
"""

from discord.ext import commands
import discord
import speech_recognition as sr
import asyncio

class BufSink(discord.reader.AudioSink):
	def __init__(self):
		self.bytes = bytearray()
		self.sample_width = 2
		self.sample_rate = 96000
		self.bytes_ps = 192000

	def write(self, data):
		self.bytes += data.data

	def freshen(self, idx):
		self.bytes = self.bytes[idx:]

class voice_commands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.tasks = {} #Guild_id: interpret task
        self.buffers = {} #Guild_id: BufSink

    @commands.command()
    @commands.is_owner()
    async def listen(self, ctx):
        """
        Connects to a vc and listens for input
        """
        if not ctx.guild.voice_client:
            vc = await ctx.author.voice.channel.connect()
        self.buffers[ctx.guild.id] = BufSink()
        self.bot.loop.run_in_executor(None, self.interpret, self.buffers[ctx.guild.id], ctx.channel)
        vc.listen(discord.reader.UserFilter(self.buffers[ctx.guild.id], ctx.author))
        await ctx.send("Joined and listening")

    def interpret(self, buffer, channel):
        """
        Interprets sound input
        """
        recog = sr.Recognizer()
        while True:
            if len(buffer.bytes) > 960000:
                idx = buffer.bytes_ps * 5
                slice = buffer.bytes[:idx]
                if any(slice):
                    idx_strip = slice.index(next(filter(lambda x: x!=0, slice)))
                    if idx_strip:
                        buffer.freshen(idx_strip)
                        slice = buffer.bytes[:idx]
                    audio = sr.AudioData(bytes(slice), buffer.sample_rate, buffer.sample_width)
                try:
                    msg = recog.recognize_wit(audio, key=self.bot.settings["wit"])
                except sr.UnknownValueError:
                    asyncio.run_coroutine_threadsafe(channel.send("Cannot interpret"), self.bot.loop)
                except sr.RequestError as e:
                    print("ERROR: Could not request results from Wit.ai service; {0}".format(e))
                if msg:
                    asyncio.run_coroutine_threadsafe(channel.send(f"Interpreted: {msg}"), self.bot.loop)
                buffer.freshen(idx)

def setup(bot):
    bot.add_cog(voice_commands(bot))