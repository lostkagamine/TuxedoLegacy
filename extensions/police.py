import re
import discord
from discord.ext import commands
import asyncio
import rethinkdb as r
import datetime

invitere = r"(http[s]?:\/\/)*discord((app\.com\/invite)|(\.gg))\/(invite\/)?(#\/)?([A-Za-z0-9\-]+)(\/)?" # my own ad regex

class Police:
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.conn

        @bot.listen('on_message_delete')
        async def on_message_delete(msg):
            g = msg.guild
            exists = (lambda: list(r.table('settings').filter(
                lambda a: a['guild'] == str(g.id)).run(self.conn)) != [])()
            has_settings = False
            if exists:
                has_settings = True
                settings = list(r.table('settings').filter(
                    lambda a: a['guild'] == str(g.id)).run(self.conn))[0]
            seconds = 60
            if has_settings:
                if 'police_enabled' not in settings.keys():
                    return
                if not settings['police_enabled']:
                    return
                if 'police_timeout' in settings.keys():
                    seconds = int(settings['police_timeout'])
            else:
                return
            if (msg.created_at + datetime.timedelta(seconds=seconds)) > datetime.datetime.now() and not msg.author.bot:
                # UNFINISHED
                embed = discord.Embed()
                embed.description = msg.content
                embed.colour = msg.author.colour
                embed.set_author(name=str(msg.author), icon_url=msg.author.avatar_url)
                embed.set_footer(text=f'This message was reposted because it was deleted too quickly. The current police cutoff is {seconds} seconds.')
                await msg.channel.send(embed=embed)
            

def setup(bot):
    bot.add_cog(Police(bot))
