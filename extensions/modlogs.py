import rethinkdb as r 
import discord
from discord.ext import commands

class ModLogs:
    def __init__(bot):
        self.bot = bot
        @bot.listen('on_member_ban')
        async def on_member_ban(g, u):
            'Placeholder'
            a = 1
