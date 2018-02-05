import datetime  # could have done wild card import but throws shit tons of warnings
from datetime import date
import discord
import faker
from discord.ext import commands


class Cnh:

    @commands.command(aliases=['cnh', 'CNH', 'calvinandhobbes'])
    async def CalvinandHobbes(self, ctx, year:int=None, month:int=None, day:int=None):
        f"""Module for Calvin and Hobbes Comics
        usage:
        {ctx.prefix}garfield (to get random comic)
        {ctx.prefix}garfield [year] [month] [day] (for specific day)
        """
        if year is None:
            fake = faker.Faker()
            # Garfield Started on 19th June, 1978
            random = fake.date_between_dates(
                date_start=datetime.date(1985, 11, 18), date_end=datetime.date(1995, 12, 31))

            year = int(random.year)
            day = int(random.day)
            month = int(random.month)
        elif year and month and day:
            randomnum = f"{year}{month:02}{day:02}"
            if int(randomnum) > 19951231  or int(randomnum) < 19851118:
                await ctx.send("please enter valid date between 1985-11-18 and 1995-12-31!!")
                return
            else:
                pass
                
        else:
            return await ctx.send("please enter valid date between 1985-11-18 and 1995-12-31!!")

        link = f"http://marcel-oehler.marcellosendos.ch/comics/ch/{year}/{month:02}/{year}{month:02}{day:02}.gif"
        embed = discord.Embed(title="Calvin and Hobbes Comics", color=0xd68717,
                              description=f"Date: {year}-{month:02}-{day:02}")

        embed.set_image(url=link)

        await ctx.send(embed=embed)


def setup(bot):
    """Calvin and Hobbles comics."""
    bot.add_cog(Cnh())
