import discord
from discord.ext import commands
from utils import lavalink


class Music:
    def __init__(self, bot):
        self.bot = bot
        self.lavalink = lavalink.Client(bot=bot, password=bot.config['LAVALINK']['PASSWORD'], loop=self.bot.loop, host=bot.config['LAVALINK']['HOST'], port=bot.config['LAVALINK']['PORT'])

        self.state_keys = {}
        self.validator = ['op', 'guildId', 'sessionId', 'event']

    @commands.command(aliases=['p'])
    async def play(self, ctx, *, query):
        player = await self.lavalink.get_player(guild_id=ctx.guild.id)

        if not player.is_connected():
            await player.connect(channel_id=ctx.author.voice.channel.id)

        query = query.strip('<>')

        if not query.startswith('http'):
            query = f'ytsearch:{query}'

        tracks = await self.lavalink.get_tracks(query)
        if not tracks:
            return await ctx.send('Nothing found 👀')

        await player.add(requester=ctx.author.id, track=tracks[0], play=True)

        embed = discord.Embed(colour=ctx.guild.me.top_role.colour,
                              title="Track Enqueued",
                              description=f'[{tracks[0]["info"]["title"]}]({tracks[0]["info"]["uri"]})')
        await ctx.send(embed=embed)

    @commands.command(aliases=['forceskip', 'fs'])
    async def skip(self, ctx):
        player = await self.lavalink.get_player(guild_id=ctx.guild.id)
        await player.skip()
        await ctx.send('Track skipped.')

    @commands.command(aliases=['np', 'n'])
    async def now(self, ctx):
        player = await self.lavalink.get_player(guild_id=ctx.guild.id)
        song = 'Nothing'
        if player.current:
            pos = lavalink.Utils.format_time(player.position)
            if player.current.stream:
                dur = 'LIVE'
            else:
                dur = lavalink.Utils.format_time(player.current.duration)
            song = f'**[{player.current.title}]({player.current.uri})**\n({pos}/{dur})'

        embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='Now Playing', description=song)
        await ctx.send(embed=embed)

    @commands.command(aliases=['q'])
    async def queue(self, ctx):
        player = await self.lavalink.get_player(guild_id=ctx.guild.id)
        queue_list = 'Nothing queued' if not player.queue else ''
        for track in player.queue:
            queue_list += f'[**{track.title}**]({track.uri})\n'

        embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='Queue', description=queue_list)
        await ctx.send(embed=embed)
    
    @commands.command(aliases=['dc'])
    async def disconnect(self, ctx):
        player = await self.lavalink.get_player(guild_id=ctx.guild.id)
        await ctx.send(f'Stopped playing and disconnected.')
        await player.disconnect()

    @commands.command()
    async def pause(self, ctx):
        player = await self.lavalink.get_player(guild_id=ctx.guild.id)
        await player.pause()
        await ctx.send(':play_pause: Paused.')

    @commands.command(aliases=['unpause'])
    async def resume(self, ctx):
        player = await self.lavalink.get_player(guild_id=ctx.guild.id)
        await player.resume()
        await ctx.send(':play_pause: Resuming...')

    @commands.command()
    async def seek(self, ctx, position:str):
        minsec = position.split(':')
        if len(minsec) != 2:
            return await ctx.send(':x: Time must be in minutes:seconds format.')
        try:
            if int(minsec[0]) < 0 or int(minsec[1]) < 0:
                return await ctx.send(':x: Time must be more than 0.')
            minms = int(minsec[0]) * 60000
            secms = int(minsec[1]) * 1000
            pos = minms + secms
        except ValueError:
            return await ctx.send(':x: Time must be in minutes:seconds format.')
        player = await self.lavalink.get_player(guild_id=ctx.guild.id)
        if not hasattr(player, 'current'):
            return await ctx.send(':x: You\'re not playing anything.')
        if player.current == None:
            return await ctx.send(':x: You\'re not playing anything.')
        if pos >= player.current.duration:
            return await ctx.send(':x: You cannot seek to a value off the end of the track.')
        await player.seek(pos)
        await ctx.send(f':control_knobs: Went to {int(minsec[0])}:{int(minsec[1])}')


    
    @commands.command(aliases=['vol', 'v'])
    async def volume(self, ctx, vol:int=100):
        if vol > 150 or vol < 0:
            return await ctx.send('Volume can range between 0 to 150.')
        player = await self.lavalink.get_player(guild_id=ctx.guild.id)
        await player.volume(vol)
        await ctx.send(f':control_knobs: Set volume to {vol}')


    async def on_voice_server_update(self, data):
        self.state_keys.update({
            'op': 'voiceUpdate',
            'guildId': data.get('guild_id'),
            'event': data
        })

        await self.verify_and_dispatch()

    async def on_voice_state_update(self, member, before, after):
        if member.id == self.bot.user.id:
            self.state_keys.update({'sessionId': after.session_id})

        await self.verify_and_dispatch()

    async def verify_and_dispatch(self):
        if all(k in self.state_keys for k in self.validator):
            await self.lavalink.dispatch_voice_update(self.state_keys)
            self.state_keys.clear()


def setup(bot):
    bot.add_cog(Music(bot))