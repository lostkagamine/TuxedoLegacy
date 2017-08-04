import json
import aiohttp
import discord
from discord.ext import commands
from datetime import datetime

with open("config.json") as f:
    config = json.load(f)

class HTTPException(Exception):
    # lul
    errtype = "HTTP"

async def get_stats(botid):
    token = config["DBOTS_TOKEN"]
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

    @commands.command(aliases=["botinfo", "getBot"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def getbot(self, ctx, *, id_arg : discord.Member):

        with ctx.channel.typing():
            if not id_arg or not ctx.guild.get_member(id_arg.id):
                return await ctx.send("This member doesn't exist.")

            print(id_arg.id)
            if not id_arg.bot:
                return await ctx.send("This member isn't a bot.")
            
            a = await get_stats(id_arg.id)
            embed = discord.Embed(
                title="Bot information for {}".format(a["name"]),
                color=0x00FF00
            )
            embed.add_field(name="Library", value=a["library"])
            embed.add_field(name="User ID", value=a["user_id"])
            owner = ctx.guild.get_member(int(a["owner_ids"][0]))
            if a["website"]:
                embed.add_field(name="Website", value="[Bot Website]({})".format(a["website"]))
            embed.add_field(name="Prefix", value="`{}`".format(a["prefix"]))
            if owner:
                embed.add_field(name="Owner", value="**{}**#{} ({})".format(owner.name, owner.discriminator, owner.id))
            if a["invite_url"]:
                embed.add_field(name="Invite", value="[Bot Invite]({})".format(a["invite_url"]))
            if not a["description"] == "":
                embed.add_field(name="Description", value=a["description"])
            embed.set_thumbnail(url=id_arg.avatar_url)
            embed.set_footer(text="Tuxedo Discord Bot Lookup | Generated at {}".format(datetime.utcnow()))

            await ctx.send(embed=embed)






def setup(bot):
    bot.add_cog(DBots(bot))