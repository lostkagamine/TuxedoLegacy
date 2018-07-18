import discord
from discord.ext import commands
import datetime
import editdistance
import re

invitere = r"(?:https?:\/\/)?discord(?:\.gg|app\.com\/invite)?\/(?:#\/)([a-zA-Z0-9-]*)" # road ad regex, thanks road
invitere2 = r"(http[s]?:\/\/)*discord((app\.com\/invite)|(\.gg))\/(invite\/)?(#\/)?([A-Za-z0-9\-]+)(\/)?" # my own regex

nosnipe = [110373943822540800]

class Snipe:
    def __init__(self, bot):
        self.bot = bot
        self.snipes = {}
        @bot.listen('on_message_delete')
        async def on_message_delete(msg):
            if msg.guild.id in nosnipe: return
            if msg.author.bot: return
            self.snipes[msg.channel.id] = msg 

        @bot.listen('on_message_edit')
        async def on_message_edit(before, after):
            if msg.guild.id in nosnipe: return
            if before.author.bot or after.author.bot: return # DEPARTMENT OF REDUNDANCY DEPARTMENT
            if editdistance.eval(before.content, after.content) >= 10 and len(before.content) > len(after.content):
                self.snipes[before.channel.id] = [before, after]

    def sanitise(self, string):
        if len(string) > 1024:
            string = string[0:1021] + "..."
        string = re.sub(invitere2, '[INVITE REDACTED]', string)
        return string

    @commands.command(description='"Snipes" someone\'s message that\'s been edited or deleted.')
    async def snipe(self, ctx):
        """"Snipes" someone's message that has been edited or deleted."""
        if ctx.guild.id in nosnipe: return
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
            emb.timestamp = snipe[0].created_at
        else: # delete snipe
            emb.set_author(name=str(snipe.author), icon_url=snipe.author.avatar_url)
            emb.description = self.sanitise(snipe.content)
            emb.colour = snipe.author.colour
            emb.timestamp = snipe.created_at
        emb.set_footer(text=f'Message sniped by {str(ctx.author)}', icon_url=ctx.author.avatar_url)
        await ctx.send(embed=emb)
        self.snipes[ctx.channel.id] = None

def setup(bot):
    bot.add_cog(Snipe(bot))
