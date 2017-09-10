import discord
from discord.ext import commands
import asyncio
import aiohttp
import json
import ast
import math
import random
import re
from utils import randomness

class Lul:
    def __init__(self, bot):
        self.bot = bot

    def dndint(self, no):
        if no == '':
            return 1
        return int(no)

    def gensuffix(self, number):
        if number == 1:
            return "st"
        elif number == 2:
            return "nd"
        elif number == 3:
            return "rd"
        else:
            return "th"

    @commands.command()
    async def cat(self, ctx):
        with ctx.channel.typing():
            with aiohttp.ClientSession() as session:
                async with session.get("http://random.cat/meow") as r:
                    r = await r.read()
                    url = json.JSONDecoder().decode(r.decode("utf-8"))["file"]
                    await ctx.send(embed=discord.Embed(title="Random Cat").set_image(url=url).set_footer(text="Powered by random.cat"))
    
    @commands.command()
    @commands.cooldown(10, 1, commands.BucketType.user)
    async def animalfact(self, ctx, _type : str):
        with ctx.channel.typing():
            sesh = aiohttp.ClientSession()
            types = []
            async with sesh.get("http://fact.birb.pw/api/v1/endpoints") as r:
                if r.status == 200:
                    data = await r.text()
                    types = ast.literal_eval(data) # safe eval, woot
                    joinedtypes = ", ".join(types)
            if _type not in types:
                sesh.close()
                return await ctx.send(f":x: Invalid type. Available types are: {joinedtypes}")
            async with sesh.get("http://fact.birb.pw/api/v1/{}".format(_type)) as r:
                if r.status == 200:
                    data = await r.text()
                    json_resp = json.loads(data)
                    fact = json_resp["string"]

                    await ctx.send(embed=discord.Embed(title="{} fact".format(_type.title()), 
                    color=randomness.random_colour(), 
                    description=fact)
                    .set_footer(text="Powered by fact.birb.pw"))
                else:
                    await ctx.send(":x: An HTTP error has occurred.")
            sesh.close()

    @commands.command(description="Number suffixes are fun.")
    async def numbermix(self, ctx):
        """ Number suffixes are fun. """
        numbers = ["fir", "seco", "thi", "four", "fif", "six", "seven", "eig", "nin", "ten"]
        suffix = ["st", "nd", "rd", "th"]
        correctlist = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eigth", "ninth", "tenth"]
        finished = []
        correct = []
        correctsuffixes = []
        for i in range(len(numbers)):
            correctsuffixes.append(self.gensuffix(i + 1))
        for i, v in enumerate(numbers):
            finished.append(v + random.choice(suffix))

        for ind, val in enumerate(finished):
            if correctlist[ind] == val:
                correct.append(val)

        correctstr = "none"
        joinedcorrect = ", ".join(correct)
        if correct != []:
            correctstr = f"{joinedcorrect} ({len(correct)}, {math.floor(len(correct) / len(correctlist) * 100)}%)"

        finishedstr = ", ".join(finished)
        if finished == correctlist:
            correctstr = "All of them! ^.^"
        await ctx.send(f"```\nOutput: {finishedstr}\nCorrect: {correctstr}```")

    @commands.command(description="Nouns.")
    async def botgen(self, ctx):
        """Get your new bot name."""
        with open("nouns.txt") as lol:
            nouns = lol.read().split('\n')
        
        await ctx.send(f'Your new bot name is `Discord {random.choice(nouns).title()}`')

    @commands.command(description='Set the bot\'s nick to something.')
    async def bnick(self, ctx, *, nick : str):
        'Set the bot\'s nick to something.'
        if not ctx.me.permissions_in(ctx.channel).change_nickname: return await ctx.send(':x: Give me Change Nickname before doing this.')
        if len(nick) > 32: return await ctx.send(':x: Give me a shorter nickname. (Limit: 32 characters)')
        await ctx.me.edit(nick=nick)
        await ctx.send(':ok_hand:')

    @commands.command(description='Roll a dice in DnD notation. (<sides>d<number of dice>)', aliases=['dice'])
    async def roll(self, ctx, dice : str):
        'Roll a dice in DnD notation. (<sides>d<number of dice>)'
        pat = re.match(r'(\d*)d(\d+)', dice)
        if pat == None:
            return await ctx.send(':x: Invalid notation! Format must be in `<rolls>d<limit>`!')
        rl = self.dndint(pat[1])
        lm = int(pat[2])
        if rl > 200: return await ctx.send(':x: A maximum of 200 dice is allowed.')
        if rl < 1: return await ctx.send(':x: A minimum of 1 die is allowed.')
        if lm > 200: return await ctx.send(':x: A maximum of 200 faces is allowed.')
        if lm < 3: return await ctx.send(':x: A minimum of 3 face is allowed.')
        roll = [random.randint(1, lm) for _ in range(rl)]
        res = ', '.join([str(i) for i in roll])
        total = 0
        for i in roll: total = total + i
        await ctx.send(f'`{res} (Total: {total})`')
        
    
# reeeeEEE you make a comment


def setup(bot):
    bot.add_cog(Lul(bot))
