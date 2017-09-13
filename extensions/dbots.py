import json
import aiohttp
import discord
from discord.ext import commands
from datetime import datetime

class HTTPException(Exception):
    # lul
    errtype = "HTTP"

async def get_stats(bot, botid):
    token = bot.config["DBOTS_TOKEN"]
    headers = {"Authorization": token}
    async with aiohttp.ClientSession() as cs:
        async with cs.get("http://bots.discord.pw/api/bots/{}".format(str(botid)), headers=headers) as r:
            r = await r.json()
            err = False
            try:
                tempvar = r["error"]
                err = True
            except KeyError:
                pass
            if err:
                raise HTTPException(r["error"])
            return r


class DBots:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["botinfo", "getBot", 'dbots'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def getbot(self, ctx, *, id_arg : discord.Member):

        with ctx.channel.typing():
            if not id_arg or not ctx.guild.get_member(id_arg.id):
                return await ctx.send("This member doesn't exist.")

            print(id_arg.id)
            if not id_arg.bot:
                return await ctx.send("This member isn't a bot.")
            
            a = await get_stats(self.bot, id_arg.id)
            embed = discord.Embed(
                title="Bot information for {}".format(a["name"]),
                color=0x00FF00
            )
            owner_ids = a["owner_ids"]
            embed.add_field(name="Library", value=a["library"])
            embed.add_field(name="User ID", value=a["user_id"])
            owner_info = []
            for i in owner_ids:
                tmpvar = ctx.guild.get_member(int(i))
                try:
                    owner_info.append(f'**{tmpvar.name}**#{tmpvar.discriminator} ({tmpvar.id})')
                except:
                    pass
            if a["website"]:
                embed.add_field(name="Website", value="[Bot Website]({})".format(a["website"]))
            embed.add_field(name="Prefix", value="`{}`".format(a["prefix"]))
            if len(owner_info) >= 1:
                embed.add_field(name="Owner" if len(owner_info) == 1 else "Owners", value="\n".join(owner_info))
            if a["invite_url"]:
                embed.add_field(name="Invite", value="[Bot Invite]({})".format(a["invite_url"]))
            if not a["description"] == "":
                embed.add_field(name="Description", value=a["description"])
            embed.set_thumbnail(url=id_arg.avatar_url)
            embed.set_footer(text="Tuxedo Discord Bot Lookup | Generated at {}".format(datetime.utcnow()))

            await ctx.send(embed=embed)






def setup(bot):
    bot.add_cog(DBots(bot))