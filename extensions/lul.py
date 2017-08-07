import discord
from discord.ext import commands
import asyncio
import aiohttp
import json
import ast
import math
import random

class Lul:
    def __init__(self, bot):
        self.bot = bot
    
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
            if _type not in types:
                sesh.close()
                return await ctx.send(":x: Invalid type")
            async with sesh.get("http://fact.birb.pw/api/v1/{}".format(_type)) as r:
                if r.status == 200:
                    data = await r.text()
                    json_resp = json.loads(data)
                    fact = json_resp["string"]

                    await ctx.send(embed=discord.Embed(title="{} fact".format(_type.title()), 
                    color=random.randint(0x000000, 0xFFFFFF), 
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
        for i in numbers:
            finished.append(i + random.choice(suffix))

        for ind, val in enumerate(finished):
            if correctlist[ind] == val:
                correct.append(val)

        correctstr = "none"
        joinedcorrect = ", ".join(correct)
        if correct != []:
            correctstr = f"{joinedcorrect} ({len(correct)}, {math.floor(len(correct) / len(correctlist) * 100)}%)"

        finishedstr = ", ".join(finished)
        if len(correctstr) == len(correctlist):
            correctstr = "All of them! ^.^"
        await ctx.send(f"```\nOutput: {finishedstr}\nCorrect: {correctstr}```")

def setup(bot):
    bot.add_cog(Lul(bot))
