import discord
import requests
from discord.ext import commands

API_URL = "https://kitsu.io/api/edge/"

#this is shit but meh...

class Kitsu:

    @commands.command()
    async def anime(self, ctx, query: str):
        """Look up anime"""
        with requests.get(API_URL + "anime", params={"filter[text]": query}) as resp:
            resp = resp.json()["data"]

            if not resp:
                return await ctx.send("The requested anime coudn't be found")

            anime = resp[0]
            title = f'{anime["attributes"]["canonicalTitle"]}'
            anime_id = anime["id"]
            url = f"https://kitsu.io/anime/{anime_id}"

            embed = discord.Embed(title=f"{title}", color=0xFFD54F, url=url)
            embed.description = anime["attributes"]["synopsis"][0:425] + "..."
            embed.add_field(name="Average Rating",
                            value=anime["attributes"]["averageRating"])
            embed.add_field(name="Popularity Rank",
                            value=anime["attributes"]["popularityRank"])
            embed.add_field(name="Age Rating",
                            value=anime["attributes"]["ageRating"])
            embed.add_field(name="Status", value=anime["attributes"]["status"])
            thing = '' if not anime['attributes']['endDate'] else f' to {anime["attributes"]["endDate"]}'
            embed.add_field(
                name="Aired", value=f"{anime['attributes']['startDate']}{thing}")
            embed.add_field(name="Episodes",
                            value=anime['attributes']["episodeCount"])
            embed.add_field(name="Type", value=anime['attributes']["showType"])
            embed.set_thumbnail(
                url=anime['attributes']["posterImage"]["original"])

            await ctx.send(embed=embed)
            
#######################################################################################################################

    @commands.command()
    async def manga(self, ctx, query: str):
        """Look up manga"""
        with requests.get(API_URL + "manga", params={"filter[text]": query}) as resp:
            resp = resp.json()["data"]

            if not resp:
                return await ctx.send("The requested manga coudn't be found")

            manga = resp[0]
            title = f'{manga["attributes"]["canonicalTitle"]}'
            manga_id = manga["id"]
            url = f"https://kitsu.io/manga/{manga_id}"

            embed = discord.Embed(title=f"{title}", color=0xFFD54F, url=url)
            embed.description = manga["attributes"]["synopsis"][0:425] + "..."
            if manga["attributes"]["averageRating"]:
                embed.add_field(name="Average Rating",
                                value=manga["attributes"]["averageRating"])
            embed.add_field(name="Popularity Rank",
                            value=manga["attributes"]["popularityRank"])
            if manga["attributes"]["ageRating"]:
                embed.add_field(name="Age Rating",
                                value=manga["attributes"]["ageRating"])
            embed.add_field(name="Status", value=manga["attributes"]["status"])
            thing = '' if not manga['attributes']['endDate'] else f' to {manga["attributes"]["endDate"]}'
            embed.add_field(
                name="Published", value=f"{manga['attributes']['startDate']}{thing}")
            if manga['attributes']['chapterCount']:
                embed.add_field(name="Chapters",
                                value=manga['attributes']["chapterCount"])
            embed.add_field(
                name="Type", value=manga['attributes']["mangaType"])
            embed.set_thumbnail(
                url=manga['attributes']["posterImage"]["original"])

            await ctx.send(embed=embed)


def setup(bot):
    """Set up the extension."""
    bot.add_cog(Kitsu())
