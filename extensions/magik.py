import asyncio
from io import BytesIO
import sys
import wand.image
import aiohttp
import base64
import discord
import random
from discord.ext import commands
from PIL import Image
import PIL.ImageOps
import PIL

messages = [
    "Igniting CPU...", 
    "am generating, plox wait", 
    "<:Thonk:341569064063336448>", 
    "Loading...", 
    "Generating Simulator 2017 is starting...", 
    "Extinguishing flames from CPU...", 
    "Shutting down CPU heatsink; Maximum performance mode activating...", 
    "Generating as fast as I can...", 
    "Overclocking..."
]

rotation_keys = {
    3: 180,
    6: 270,
    8: 90
}

async def get_img_from_url(url):
    """ Returns image bytes from URL data """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            response = await r.read()

    img = BytesIO(response) #get_bytes(BytesIO(response))
    return img

def perform_operations(img):
    """ Performs some magik on the image """
    img.format = "png"
    img.alpha_channel = True
    img.transform(resize="400x400")
    img.liquid_rescale(width=int(img.width * 0.5),
                       height=int(img.height * 0.5),
                       delta_x=int(0.5 * 1),
                       rigidity=0)
    img.liquid_rescale(width=int(img.width * 1.5),
                       height=int(img.height * 1.5),
                       delta_x=2,
                       rigidity=0)
    return img

def invert_colours(img):
    """Inverts the image's colours"""
    img.format = "png"
    img.alpha_channel = True
    img.transform(resize="400x400")


async def make_magik(loop, data):
    """ Start Function """
    b = BytesIO()
    with wand.image.Image(file=data) as i:
        i = await loop.run_in_executor(None, perform_operations, i)
        i.save(file=b)
    b.seek(0)
    return b

def invert_colours(data):
    """ Start Function """
    inversion = PIL.Image.open(data)
    b = BytesIO()
    if inversion.mode == "RGBA":
        red,green,blue,alpha = inversion.split()
        rgb_inv = PIL.Image.merge("RGB", (red,green,blue))
        result = PIL.ImageOps.invert(rgb_inv)
    else:
        result = PIL.ImageOps.invert(inversion)
    result.save(b, "PNG")
    b.seek(0)
    return b


class Magik:
    def __init__(self, bot):
        self.bot = bot
        self.loop = asyncio.get_event_loop()

    @commands.command(pass_context=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def magik(self, ctx, target, times = 1):
        try:
            member = await commands.MemberConverter().convert(ctx, target)
            url = member.avatar_url
        except Exception as e:
            url = target
        try:
            msg_index = random.randint(0,len(messages) - 1)
            tmp = await ctx.send(messages[msg_index] + " (Started)")
            with ctx.message.channel.typing():
                data = await get_img_from_url(url)
                # if times > 10:
                #     await tmp.delete()
                #     return await ctx.send(":x: You can only do a maximum of 10 passes.")
                for i in range(0, times):
                    calc = i / int(times)
                    lastpc = 0
                    if calc >= 0.75 and lastpc <= 0.75:
                        lastpc = 1
                        await tmp.edit(content="{} (75%)".format(messages[msg_index]))
                    elif calc >= 0.5 and lastpc <= 0.5:
                        lastpc = 0.75
                        await tmp.edit(content="{} (50%)".format(messages[msg_index]))
                    elif calc >= 0.25 and lastpc <= 0.25:
                        lastpc = 0.5
                        await tmp.edit(content="{} (25%)".format(messages[msg_index]))
                    data = await make_magik(self.loop, data)
                await tmp.edit(content="{} (Sending)".format(messages[msg_index]))
                await ctx.send(file=discord.File(data, filename="magik.png"))
                await tmp.delete()
        except Exception as e:
            await tmp.delete()
            await ctx.send(":x: Error! Make sure you provided a valid @mention or URL / passes value!\n\n```{}: {}```".format(type(e).__name__, e))

    @commands.command(pass_context=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def invert(self, ctx, target):
        try:
            member = await commands.MemberConverter().convert(ctx, target)
            url = member.avatar_url
        except Exception as e:
            url = target
        try:
            img = await get_img_from_url(url)
            iimg = invert_colours(img)
            await ctx.send(file=discord.File(iimg, filename="inverted.png"))
        except Exception as e:
            await ctx.send(":x: Error! Make sure you provided a valid @mention or URL!\n\n```{}: {}```".format(type(e).__name__, e))

def setup(bot):
    bot.add_cog(Magik(bot))