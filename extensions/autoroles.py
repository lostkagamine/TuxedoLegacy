import discord
from discord.ext import commands
import asyncio
import rethinkdb as r

class Autoroles:
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.conn