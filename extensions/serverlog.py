import discord
from discord.ext import commands


class serverlog:

    def __init__(self, bot):
        self.bot = bot


    async def on_guild_join(self, guild):
        total = str(len(self.bot.guilds))
        embed = discord.Embed(color=0x76FF03) 
        embed.description = f"I just joined __**{guild.name}**__ so the total number of guilds is: __**{total}**__"
        embed.set_thumbnail(url=guild.icon_url)
        embed.add_field(name="Owner", value=str(guild.owner))
        embed.add_field(name="ID", value=str(guild.id))
        embed.add_field(name="Members", value=len(guild.members))
        embed.add_field(name="Humans", value=len(guild.members) - len([a for a in guild.members if a.bot]))
        embed.add_field(name="Bots", value=len([a for a in guild.members if a.bot]))
        embed.add_field(name="Text channels", value=len(guild.text_channels))
        embed.add_field(name="Voice channels", value=len(guild.voice_channels))
        embed.add_field(name="Region", value=str(guild.region))

        await self.bot.get_guild(403967731025707009).get_channel(410458514310561792).send(embed=embed)



    async def on_guild_remove(self, guild):
        total = str(len(self.bot.guilds))
        embed = discord.Embed(color=0xFF1744)
        embed.description = f"I just left __**{guild.name}**__ so the total number of guilds is: __**{total}**__" 
        embed.set_thumbnail(url=guild.icon_url)
        embed.add_field(name="Owner", value=str(guild.owner))
        embed.add_field(name="ID", value=str(guild.id))
        embed.add_field(name="Members", value=len(guild.members))
        embed.add_field(name="Humans", value=len(guild.members) - len([a for a in guild.members if a.bot]))
        embed.add_field(name="Bots", value=len([a for a in guild.members if a.bot]))
        embed.add_field(name="Text channels", value=len(guild.text_channels))
        embed.add_field(name="Voice channels", value=len(guild.voice_channels))
        embed.add_field(name="Region", value=str(guild.region))

        await self.bot.get_guild(403967731025707009).get_channel(410458514310561792).send(embed=embed)

def setup(bot):
    bot.add_cog(serverlog(bot))
