import os

import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import textwrap


class Memes:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["ds", "DS"])
    async def dipshit(self, ctx, msg: discord.Member=None):
        """Generate a meme
        usage : %prefix%dipshit <mention user>
        """
        if msg:
            msg = msg.name
        else:
            msg = ctx.author.name

        image = Image.open("data/google.jpg").convert("RGBA")
        txt = Image.new('RGBA', image.size, (255, 255, 255, 0))

        font = ImageFont.truetype('data/fonts/arial.ttf', 18)

        d = ImageDraw.Draw(txt)

        d.text((138, 58), msg, font=font, fill=(0, 0, 0, 255))

        out = Image.alpha_composite(image, txt).save("dipshit.png")

        file = discord.File("dipshit.png", filename="dipshit.png")
        await ctx.trigger_typing()
        await ctx.send(file=file)
        os.remove('dipshit.png')

def setup(bot):
    bot.add_cog(Memes(bot))
