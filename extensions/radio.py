from extensions import help, music

from discord.ext import commands


class Radio:

    @commands.group()
    async def radio(self, ctx):
        """Play radio from Listen.moe"""
        if not ctx.invoked_subcommand:
            await help.help(ctx, "radio")

    @radio.command()
    async def start(self, ctx):
        player = ctx.bot.lavalink.players.get(ctx.guild.id)
        if not player.is_connected:
            if ctx.author.voice is None or ctx.author.voice.channel is None:
                return await ctx.send('Join a voice channel!')
            player.store('channel', ctx.channel.id)
            await player.connect(ctx.author.voice.channel.id)
        else:
            if ctx.author.voice is None or ctx.author.voice.channel is None or player.connected_channel.id != ctx.author.voice.channel.id:
                return await ctx.send('Join my voice channel!')

        await player.add_and_play(requester=ctx.author.id, track="https://listen.moe/stream")
        await ctx.send("radio started")

    @commands.command()
    async def stop(self, ctx):
        player = ctx.bot.lavalink.players.get(ctx.guild.id)

        if not player.is_playing:
            return await ctx.send('Not playing.')

        player.queue.clear()
        await player.stop()
        await ctx.send('⏹ | Stopped.')


def setup(bot):
    bot.add_cog(Radio(bot))
