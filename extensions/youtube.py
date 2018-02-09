from urllib import parse

import requests
from bs4 import BeautifulSoup
from discord.ext import commands


class Youtube:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, aliases=['yt', 'vid', 'video'])
    async def youtube(self, ctx, *, msg):
        """Search for videos on YouTube"""
        search = parse.quote(msg)
        response = requests.get(
            "https://www.youtube.com/results?search_query={}".format(search), verify=False).text
        result = BeautifulSoup(response, "html.parser")
        await ctx.send("https://www.youtube.com{}".format(result.find_all(attrs={'class': 'yt-uix-tile-link'})[0].get('href')))


def setup(bot):
    bot.add_cog(Youtube(bot))
