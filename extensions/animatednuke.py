import re
import discord
from discord.ext import commands
import rethinkdb as r # do i even need this tbh, i prolly dont  
from utils import database

REGEXP = r'<a:.*:\d*>'

class AnimatedEmojiNuke:
    def __init__(self, bot):
        self.bot = bot
        @bot.listen('on_message')
        async def on_message(msg):
            if re.search(REGEXP, msg.content) != None:
                if database.check_setting(bot.conn, msg.guild, 'no_animated_emojis'):
                    try:
                        await msg.delete()
                        await msg.channel.send(f':no_entry_sign: **{msg.author.display_name}**, animated emojis aren\'t permitted here.')
                    except discord.Forbidden:
                        return

# literally it

def setup(bot):
    bot.add_cog(AnimatedEmojiNuke(bot))
