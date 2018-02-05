import requests
import discord
import json
import codecs
from bs4 import BeautifulSoup
from discord.ext import commands


class Translate:

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def translate(self, ctx, lang_to_trans, *, msg):
        """Translates words from one language to another. Do `tux help`translate for more information.
        Usage:
        `tux translate <language you wanna translate>` <words>` - Translate words from one language to another. Full language names must be used.
        The original language will be assumed automatically.
        """
        some_var = requests.get(
            "https://cdn.discordapp.com/attachments/407783970558836740/410076802762014720/langs.json", verify=False).text
        language_codes = json.loads(some_var)
        real_language = False
        lang_to_trans = lang_to_trans.lower()
        for entry in language_codes:
            if lang_to_trans in language_codes[entry]["name"].replace(";", "").replace(",", "").lower().split():
                language = language_codes[entry]["name"].replace(
                    ";", "").replace(",", "").split()[0]
                lang_to_trans = entry
                real_language = True
        if real_language:
            translate = requests.get(
                "https://translate.google.com/m?hl={}&sl=auto&q={}".format(lang_to_trans, msg), verify=False).text
            result = str(translate).split('class="t0">')[1].split("</div>")[0]
            result = BeautifulSoup(result, "lxml").text
            embed = discord.Embed(color=discord.Color.blue())
            embed.add_field(name="Original", value=msg, inline=False)
            embed.add_field(name=language, value=result.replace(
                "&amp;", "&"), inline=False)
            if result == msg:
                embed.add_field(
                    name="**Warning**", value="Google Translate doesn't support this language.")
            await ctx.send("", embed=embed)
        else:
            await ctx.send("Enter a real language please.")


def setup(bot):
    bot.add_cog(Translate(bot))
