import datetime  # could have done wild card import but throws shit tons of warnings
from datetime import date
import discord
import faker
from discord.ext import commands


class Garfield:

    @commands.command(aliases=['GC', "Gc", "garfield", "Garfield"])
    async def gc(self, ctx, year:int=None, month:int=None, day:int=None):
        f"""Module for Garfield Comics
        usage:
        {ctx.prefix}garfield (to get random comic)
        {ctx.prefix}garfield [year] [month] [day] (for specific day)
        """
        if year is None:
            fake = faker.Faker()
            # Garfield Started on 19th June, 1978
            random = fake.date_between_dates(
                date_start=datetime.date(1978, 6, 19), date_end=None)

            year = int(random.year)
            day = int(random.day)
            month = int(random.month)
        elif year and month and day:
            randomnum = f"{year}{month:02}{day:02}"
            owo = date.today()
            todays_date = f"{owo.year}{owo.month:02}{owo.day:02}"
            if int(randomnum) > int(todays_date) or int(randomnum) < 19780619:
                await ctx.send("please enter valid date!!")
                return
            else:
                pass
                
        else:
            return await ctx.send("please enter valid date!!")

        link = f"https://d1ejxu6vysztl5.cloudfront.net/comics/garfield/{year}/{year}-{month:02}-{day:02}.gif"
        embed = discord.Embed(title="Garfield Comics", color=0xd68717,
                              description=f"Date: {year}-{month:02}-{day:02}")

        embed.set_image(url=link)

        await ctx.send(embed=embed)


def setup(bot):
    """Garfield comics."""
    bot.add_cog(Garfield())
