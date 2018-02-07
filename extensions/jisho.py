#!/usr/bin/env python3

"""jisho.org query command."""

import urllib.parse
import random

import discord
from discord.ext import commands

BASE_URL = "http://jisho.org/api/v1/search/words?"


class Jisho:
    """A Japanese translation command."""

    @commands.command(aliases=["jp"])
    async def jisho(self, ctx, query, *args):
        f"""Translate a word into Japanese.

        Example usage:
        {ctx.prefix}jisho test
        """
        query = f"{query} {' '.join(args)}"
        params = urllib.parse.urlencode({"keyword": query})
        url = BASE_URL + params
        async with ctx.bot.session.get(url) as response:
            if response.status == 200:
                data = await response.json()

                if not data["data"]:
                    await ctx.send("No matching result found on jisho.org.")

                jap = data["data"][0]["japanese"][0]
                senses = data["data"][0]["senses"][0]
                defs = ", ".join(senses["english_definitions"])
                tags = senses["tags"]

                embed = discord.Embed(color=discord.Color.blurple())
                embed.add_field(name="Kanji", value=str(jap.get("word")))
                embed.add_field(name="Kana", value=str(
                    jap.get("reading")), inline=False)
                embed.add_field(name="English", value=defs, inline=False)
                embed.add_field(name="Tags", value=tags)
                embed.set_thumbnail(
                    url="https://www.tofugu.com/images/learn-japanese/jisho-org-9a549ffd.jpg")
                embed.set_footer(text="Powered by Jisho.org")
                await ctx.send(embed=embed)

            else:
                await ctx.send("Couldn't reach Jisho.org")


def setup(bot):
    """Set up the extension."""
    bot.add_cog(Jisho())
