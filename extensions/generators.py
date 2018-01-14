import asyncio
import wand.image
import aiohttp
import discord

from discord.ext import commands
from io import BytesIO
from PIL import Image, ImageOps
from utils import parsers

class Generators:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def magik(self, ctx, target, *args):
        """ Add some magik to your boring-ass images """
        try:
            member = await commands.MemberConverter().convert(ctx, target)
            url = member.avatar_url_as(format='png')
        except:
            url = target
        
        url = url.replace("gif", "png").strip("<>")

        if args:
            opt = args[0]
        else:
            opt = 0.5
        multi = parsers.as_number(opt, 0.5)
        if multi > 10 or multi < 1:
            return await ctx.send('Maximum multiplier is 10, minimum multiplier is 1')

        m = await ctx.send("pls wait am generating")
        try:
            b = BytesIO()
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as r:
                    with wand.image.Image(file=BytesIO(await r.read())) as img:
                        img.transform(resize="400x400")
                        img.liquid_rescale(width=int(img.width * 0.5),
                                           height=int(img.height * 0.5),
                                           delta_x=multi,
                                           rigidity=0)
                        img.liquid_rescale(width=int(img.width * 1.5),
                                           height=int(img.height * 1.5),
                                           delta_x=2,
                                           rigidity=0)
                        img.save(file=b)
                        b.seek(0)

            await ctx.send(file=discord.File(b, filename="magik.png"))
            await m.delete()
        except:
            await m.edit(content="Unable to generate image. Provide a mention or valid URL.")

    @commands.command()
    @commands.cooldown(1, 25, commands.BucketType.user)
    async def invert(self, ctx, target):
        """ Ever wanted to see the stuff of nightmares? """
        try:
            member = await commands.MemberConverter().convert(ctx, target)
            url = member.avatar_url
        except:
            url = target
        
        url = url.replace("gif", "png").strip("<>")
        m = await ctx.send("pls wait am generating")

        try:
            b = BytesIO()
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as r:
                    img = Image.open(BytesIO(await r.read()))
                    bio = BytesIO()

                    if (img.mode == 'RGBA'):
                        r,g,b,a = img.split()
                        rgb_image = Image.merge('RGB', (r,g,b))
                        inverted = ImageOps.invert(rgb_image)
                        r,g,b = inverted.split()
                        img = Image.merge('RGBA', (r,g,b,a))
                    else:
                        img = ImageOps.invert(img)

                    img.save(bio, "PNG")
                    bio.seek(0)
                    await ctx.send(file=discord.File(bio, filename="invert.png"))
                    await m.delete()
        except Exception as e:
            print(e)
            await m.edit(content="Unable to generate image. Provide a mention or valid URL.")

def setup(bot):
    bot.add_cog(Generators(bot))