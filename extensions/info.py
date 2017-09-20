import math
import os
import cpuinfo
import discord
from discord.ext import commands
import psutil


def propcheck(prop, d):
    return d[prop] if d[prop] else "None"

class Info:
    def __init__(self, bot):
        self.bot = bot

    def humanbytes(self, B): # function lifted from StackOverflow :mmLol:
        'Return the given bytes as a human friendly KB, MB, GB, or TB string'
        B = float(B)
        KB = float(1024)
        MB = float(KB ** 2) # 1,048,576
        GB = float(KB ** 3) # 1,073,741,824
        TB = float(KB ** 4) # 1,099,511,627,776

        if B < KB:
            return '{0} {1}'.format(B,'Bytes' if 0 == B > 1 else 'Byte')
        elif KB <= B < MB:
            return '{0:.2f} KB'.format(B/KB)
        elif MB <= B < GB:
            return '{0:.2f} MB'.format(B/MB)
        elif GB <= B < TB:
            return '{0:.2f} GB'.format(B/GB)
        elif TB <= B:
            return '{0:.2f} TB'.format(B/TB)


    @commands.command(aliases=["support", "guild"])
    async def server(self, ctx):
        text = "**Support Server**\n\nIf you're encountering a problem with Tuxedo, or just wanna drop by, use this Discord link to join the official Tuxedo server.\n\nLink => https://discord.gg/KEcme4H"
        try:
            await ctx.author.send(text)
            await ctx.send(":mailbox_with_mail: Check your DMs.")
        except discord.Forbidden:
            await ctx.send(text)

    @commands.command(aliases=['info', 'stats'])
    async def about(self, ctx):
        mem = psutil.virtual_memory()
        currproc = psutil.Process(os.getpid())
        print(mem)
        total_ram = self.humanbytes(mem[0])
        available_ram = self.humanbytes(mem[1])
        usage = self.humanbytes(currproc.memory_info().rss)
        text = f"""
```ini
[ Tuxedo ]
An open-source moderation bot for Discord
Made by ry00001 in Python 3.6 using Discord.py
Source code freely available at https://github.com/ry00000/Tuxedo

[ Stats ]
Total RAM: {total_ram}
Available RAM: {available_ram}
RAM used by bot: {usage}
Number of bot commands: {len(ctx.bot.commands)}
Number of guilds: {len(ctx.bot.guilds)}
Number of users: {len(ctx.bot.users)}

[ Credits ]
HexadecimalPython: Original core
Liara: eval
Devoxin: Hosting and rewritten core

[ Special thanks ]
Ryosuke™
The entirety of Discord Bots
All my awesome users!
```
        """

        await ctx.send(text)

def setup(bot):
    bot.add_cog(Info(bot))
