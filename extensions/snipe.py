import discord
from discord.ext import commands
import datetime
import editdistance

class Snipe:
    def __init__(self, bot):
        self.bot = bot
        self.snipes = {}
        @bot.listen('on_message_delete')
        async def on_message_delete(msg):
            if msg.author.bot: return
            self.snipes[msg.channel.id] = msg 

        @bot.listen('on_message_edit')
        async def on_message_edit(before, after):
            if before.author.bot or after.author.bot: return # DEPARTMENT OF REDUNDANCY DEPARTMENT
            if editdistance.eval(before.content, after.content) >= 10:
                self.snipes[before.channel.id] = [before, after]

    def sanitise(self, string):
        if len(string) > 1024:
            string = string[0:1021] + "..."
        return string

    @commands.command(description='"Snipes" someone\'s message that\'s been edited or deleted.')
    async def snipe(self, ctx):
        '"Snipes" someone\'s message that\'s been edited or deleted.'
        try:
            snipe = self.snipes[ctx.channel.id]
        except KeyError:
            return await ctx.send('No snipes in this channel!')
        if snipe == None:
            return await ctx.send('No snipes in this channel!')
        # there's gonna be a snipe after this point
        emb = discord.Embed()
        if type(snipe) == list: # edit snipe
            emb.set_author(name=str(snipe[0].author), icon_url=snipe[0].author.avatar_url)
            emb.colour = snipe[0].author.colour
            emb.add_field(name='Before', value=self.sanitise(snipe[0].content), inline=False)
            emb.add_field(name='After', value=self.sanitise(snipe[1].content), inline=False)
        else: # delete snipe
            emb.set_author(name=str(snipe.author), icon_url=snipe.author.avatar_url)
            emb.description = snipe.content
            emb.colour = snipe.author.colour
        emb.set_footer(text=f'Message sniped by {str(ctx.author)}', icon_url=ctx.author.avatar_url)
        emb.timestamp = datetime.datetime.now()
        await ctx.send(embed=emb)
        self.snipes[ctx.channel.id] = None

def setup(bot):
    bot.add_cog(Snipe(bot))
