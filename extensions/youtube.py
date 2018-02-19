from urllib import parse

import aiohttp
from bs4 import BeautifulSoup
from discord.ext import commands


class Youtube:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['yt', 'vid', 'video'])
    async def youtube(self, ctx, query: str):
        """Search for videos on YouTube"""
        search = parse.quote(query)
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f"https://www.youtube.com/results?search_query={search}") \
                .text()
        result = BeautifulSoup(response, "html.parser")
        await ctx.send("https://www.youtube.com{}".format(
            result.find_all(attrs={'class': 'yt-uix-tile-link'})[0]
                  .get('href')))


def setup(bot):
    bot.add_cog(Youtube(bot))
