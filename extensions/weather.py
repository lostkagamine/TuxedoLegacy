from PIL import Image
import urllib.request
import os
from discord.ext import commands
import discord

#the file names are memes, pls ignore..kthx

class Weather:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def weather(self, ctx, city: str=None):
        URL = f"http://wttr.in/{city}_2tnp_transparency=1000_lang=en.png"

        if not city:
            await ctx.send("Please enter a valid city / town")
        else:
            with urllib.request.urlopen(URL) as url:
                with open("temp.png", "wb") as f:
                    f.write(url.read())

            img = Image.open('temp.png')

            img2 = img.crop((0, 0, 467, 398)).save("img2.png")

            file = discord.File("img2.png", filename="weather.png")
            await ctx.trigger_typing()
            await ctx.send(file=file)
            os.remove('img2.png')
            os.remove("temp.png")

    @commands.command()
    async def moon(self, ctx):
        URL = "http://wttr.in/moon.png"
        
        with urllib.request.urlopen(URL) as url:
            with open("temp8.png", "wb") as f:
                f.write(url.read())

        img = Image.open('temp8.png')

        img2 = img.crop((0, 0, 326, 317)).save("img8.png")

        file = discord.File("img8.png", filename="moon.png")
        await ctx.trigger_typing()
        await ctx.send(file=file)
        os.remove('img8.png')
        os.remove("temp8.png")


def setup(bot):
    bot.add_cog(Weather(bot))
