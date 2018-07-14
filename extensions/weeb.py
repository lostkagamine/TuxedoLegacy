#!/usr/bin/env python3

"""Contains a cog for various weeb reaction commands."""

import random
import requests
import json

import discord
from discord.ext import commands


BASE_URL_API = "https://api.weeb.sh/images/random?type={0}"

async def message_generator(ctx, thing: str=None, user: str=discord.Member):
    """Generate a message based on the user."""
    if not thing or not user:
        message = ""
    elif user.id == ctx.bot.user.id:
        message = f"Aw you so cute, thanks :3"
    elif user.id == ctx.author.id:
        message = random.choice(("Aww okay :3",
                                 f"have a {thing} you big piece of fluff ball x3",
                                 ":3",
                                 "x3"))
    else:
        message = f"**{user.display_name}**, you got a {thing} from **{ctx.author.display_name}!**"
    return message


async def weeb_maker(ctx, thing: str, message: str=""):
    """A helper function that grabs an image and posts it in response to a user.

     thing - Image type.
     user - user (duh).
    """
    token = ctx.bot.config.get("weeb_token")
    url = BASE_URL_API.format(thing)
    headers = {"Authorization": f"Bearer {token}"}
    with requests.get(url, headers=headers) as response:
        data = response.json()
        if data:
            c = random.randint(0, 16777215)
            url = data['url']
            embed = discord.Embed(title=None, color=c)
            embed.set_image(url=url)
            embed.set_footer(text="Powered by weeb.sh")
            await ctx.send(message, embed=embed)
        else:
            message = "Unable to retrive image, blame Wolke"
            await ctx.send(message)


class Weeb:
    """Weeb reaction commands."""

    @commands.command()
    async def cuddle(self, ctx, *, user: discord.Member):
        """Cuddle a user"""
        message = await message_generator(ctx, "cuddle", user)
        await weeb_maker(ctx, "cuddle", message)

    @commands.command()
    async def hug(self, ctx, *, user: discord.Member):
        """Hug a user"""
        message = await message_generator(ctx, "hug", user)
        await weeb_maker(ctx, "hug", message)

    @commands.command()
    async def kiss(self, ctx, *, user: discord.Member):
        """Kiss a user"""
        message = await message_generator(ctx, "kiss", user)
        await weeb_maker(ctx, "kiss", message)

    @commands.command(aliases=["2lewd", "2lewd4me"])
    async def lewd(self, ctx):
        """Lewd"""
        await weeb_maker(ctx, "lewd")

    @commands.command()
    async def lick(self, ctx, *, user: discord.Member):
        """Lick a user"""
        message = await message_generator(ctx, "lick", user)
        await weeb_maker(ctx, "lick", message)

    @commands.command()
    async def nom(self, ctx):
        """Nom"""
        await weeb_maker(ctx, "nom")

    @commands.command(aliases=['nya', 'meow', 'nyan'])
    async def _neko(self, ctx):
        """Nyan"""
        await weeb_maker(ctx, "neko", f"{ctx.invoked_with.capitalize()}~")

    @commands.command()
    async def owo(self, ctx):
        """owo"""
        await weeb_maker(ctx, "owo")

    @commands.command()
    async def awoo(self, ctx):
        """awoo"""
        await weeb_maker(ctx, "awoo")

    @commands.command(aliases=["headpat", "pet"])
    async def pat(self, ctx, *, user: discord.Member):
        """Pat a user"""
        message = await message_generator(ctx, "pat", user)
        await weeb_maker(ctx, "pat", message)

    @commands.command()
    async def pout(self, ctx):
        """Pout"""
        await weeb_maker(ctx, "pout")

    @commands.command()
    async def slap(self, ctx, *, user: discord.Member):
        """Slap a user"""
        message = await message_generator(ctx, "slap", user)
        await weeb_maker(ctx, "slap", message)

    @commands.command()
    async def smug(self, ctx):
        """Smug"""
        await weeb_maker(ctx, "smug")

    @commands.command()
    async def stare(self, ctx, *, user: discord.Member):
        """Stare at a user"""
        message = await message_generator(ctx, "stare", user)
        await weeb_maker(ctx, "stare", message)

    @commands.command()
    async def tickle(self, ctx, *, user: discord.Member):
        """Tickle a user"""
        message = await message_generator(ctx, "tickle", user)
        await weeb_maker(ctx, "tickle", message)

    @commands.command()
    async def triggered(self, ctx):
        """Triggered"""
        await weeb_maker(ctx, "triggered")

    @commands.command()
    async def blush(self, ctx):
        """blush"""
        await weeb_maker(ctx, "blush")

    @commands.command()
    async def bang(self, ctx):
        """bang"""
        await weeb_maker(ctx, "bang")

    @commands.command()
    async def jojo(self, ctx):
        """jojo"""
        await weeb_maker(ctx, "jojo")

    @commands.command(aliases=["megu", "Megu"])
    async def megumin(self, ctx):
        """Triggered"""
        await weeb_maker(ctx, "megumin")

    @commands.command(aliases=["Rem"])
    async def rem(self, ctx):
        """rem"""
        await weeb_maker(ctx, "rem")

    @commands.command()
    async def wag(self, ctx):
        """wag"""
        await weeb_maker(ctx, "wag")

    @commands.command(aliases=["waifuinsult", 'waifuin'])
    async def waifu_insult(self, ctx):
        """insult waifuuuu"""
        await weeb_maker(ctx, "waifu_insult")

    @commands.command()
    async def wasted(self, ctx):
        """wasted"""
        await weeb_maker(ctx, "wasted")

    @commands.command()
    async def sumfuk(self, ctx):
        """owowow"""
        await weeb_maker(ctx, "sumfuk")

    @commands.command()
    async def dab(self, ctx):
        """dab"""
        await weeb_maker(ctx, "dab")

    @commands.command(aliases=["dmemes", "dismemes"])
    async def discord_memes(self, ctx):
        """memes"""
        await weeb_maker(ctx, "discord_memes")

    @commands.command(aliases=["delet"])
    async def delet_this(self, ctx):
        """jojo"""
        await weeb_maker(ctx, "delet_this")

    @commands.command()
    async def nani(self, ctx):
        """nani?"""
        await weeb_maker(ctx, "nani")


def setup(bot):
    """Setup function for reaction images."""
    bot.add_cog(Weeb())
