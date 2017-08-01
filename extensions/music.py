import asyncio

import discord
import youtube_dl

from discord.ext import commands

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, ytdl.extract_info, url)

        if "entries" in data:
            data = data["entries"][0]

        filename = ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Music:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["j"])
    async def join(self, ctx, *, channel : discord.VoiceChannel = None):
        """Joins voice"""
        if channel is None:
            if ctx.author.voice is None:
                return await ctx.send(":x: Join a voice channel or pass one as a parameter.")
            else:
                return await ctx.author.voice.channel.connect()

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command(aliases=["d", "dc"])
    async def disconnect(self, ctx):
        """Disconnects from voice"""
        if ctx.voice_client is not None:
            return await ctx.voice_client.disconnect()
        else:
            return await ctx.send(":x: I'm not connected!")

    @commands.command(aliases=["yt", "p", "youtube"])
    async def play(self, ctx, *, url):
        """Plays a URL"""

        url = url.strip("<>")

        if ctx.voice_client is None:
            if ctx.author.voice.channel:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send(":x: Join a voice channel or run `join <channel>`")
            
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        player = await YTDLSource.from_url(url, loop=self.bot.loop)
        ctx.voice_client.play(player, after=lambda e: print("Player error: {}".format(e)) if e else None)

    @commands.command(aliases=["vol"])
    async def volume(self, ctx, volume : int):
        """Volume control"""

        if ctx.voice_client is None:
            return await ctx.send(":x: I'm not connected!")

        ctx.voice_client.source.volume = volume
        await ctx.send("Changed volume to {}%".format(volume))

def setup(bot):
    bot.add_cog(Music(bot))