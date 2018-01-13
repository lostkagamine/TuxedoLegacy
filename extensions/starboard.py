import discord
from discord.ext import commands
from utils import database, randomness
import datetime, random

# Tuxedo starboard module
# Don't steal pls, it's FOSS but don't thanks. 
# very basic, will expand later:tm:

class Starboard:
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.conn

    async def on_reaction_add(self, r, u):
        name = r.emoji if type(r.emoji) == str else r.emoji.name # may as well
        count = r.count
        settings = database.get_settings(self.conn, r.message.guild) # grab me all the settings
        if not settings:
            return # oops, no settings
        if not 'starboard_channel' in settings.keys():
            return # oops, no sb channel
        min_count = database.check_setting(self.conn, r.message.guild, 'starboard_min_count') or 1
        sb_name = database.check_setting(self.conn, r.message.guild, 'starboard_emote') or '⭐'
        channel = database.check_setting(self.conn, r.message.guild, 'starboard_channel')
        channel = r.message.guild.get_channel(int(channel)) # get proper channel
        if channel is None:
            return # no more starboard channel, and we don't wanna throw an exception now do we
        if name == sb_name and count >= min_count:
            e = discord.Embed(colour=randomness.random_colour())
            e.set_author(name=str(r.message.author), icon_url=r.message.author.avatar_url_as(format='png'))
            e.description = r.message.content
            e.timestamp = datetime.datetime.utcnow()
            e.title = f'{random.choice([':star:', ':star2:', ':dizzy:'])} **{count}** <#{r.message.channel.id}>'
            await channel.send(embed=e)

def setup(bot):
    bot.add_cog(Starboard(bot))
