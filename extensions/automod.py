import discord
from discord.ext import commands
import rethinkdb as r
from utils import database
import re

irg = r'(http(s*):\/\/)*discord(app)*\.(com|gg)\/(invite\/)*([A-Za-z])+'
irg = re.compile(irg)

# WHEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE
# Tuxedo automod cog, this won't work in other bots
# I don't condone sticking this in a redbot as it probably won't work and redbots are bad anyways so don't do it

class Automod:
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.conn
        self.warnings = {}

    async def on_message(self, msg):
        perms = msg.author.permissions_in(msg.channel)
        if (
            perms.kick_members or
            perms.ban_members or
            perms.manage_roles
        ): return # make staff immune to automod
        invite = re.search(irg, msg.content)
        if invite and database.check_setting(self.conn, msg.guild, 'invite_automod'): # is an invite *and* the guild has invite killing enabled
            self._add_warning(msg.author.id)
            if self._get_warnings(msg.author.id) > 3:
                await msg.delete()
                await msg.guild.ban(msg.author, reason='[Automatic - advertising too much]')
                await msg.channel.send(f':hammer: | {msg.author} has been **banned** automatically for advertising.')
                self.warnings[msg.author.id] = 0
            elif self._get_warnings(msg.author.id) == 2:
                await msg.delete()
                await msg.guild.kick(msg.author, reason='[Automatic - advertising too much]')
                await msg.channel.send(f':hammer: | {msg.author} has been **kicked** automatically for advertising.')
            elif self._get_warnings(msg.author.id) == 1:
                await msg.delete()
                await msg.channel.send(f':no_entry_sign: | <@{msg.author.id}>, advertising isn\'t allowed in this server.')

    def _get_warnings(self, uid:int):
        try:
            return self.warnings[uid]
        except KeyError:
            return 0

    def _add_warning(self, uid:int, count=1):
        try:
            w = self.warnings[uid]
        except KeyError:
            w = 0
        w += count
        self.warnings[uid] = w

def setup(bot):
    bot.add_cog(Automod(bot))
