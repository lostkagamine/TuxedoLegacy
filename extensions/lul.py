import discord
from discord.ext import commands
import asyncio
import aiohttp
import json

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


def setup(bot):
    bot.add_cog(Lul(bot))
