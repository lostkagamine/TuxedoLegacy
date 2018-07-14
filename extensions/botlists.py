import discord 
from discord.ext import commands

import aiohttp
import addict

ROOT_URL = 'https://discordbots.org/api/widget/!ID!.png'
ROOT_API_URL = 'https://discordbots.org/api/bots/!ID!'

def prepare(stri, bot_id):
    return stri.replace('!ID!', str(bot_id))

class BotLists:
    # Commands for use with bot lists, eg DBots or DBL.
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def vote(self, ctx):
        await ctx.send(f'''If you like me and want to support my developer in aiming for certification, vote for me on DiscordBots.org!
You may do so using this link:
https://discordbots.org/bot/{ctx.me.id}/vote
Any vote helps!''')

    @commands.command()
    async def dbl(self, ctx, bot: discord.Member):
        # do checks
        cs = aiohttp.ClientSession()
        async with cs.get(prepare(ROOT_API_URL, bot.id)) as res:
            if res.status != 200:
                return await ctx.send(':x: | Either this bot is not listed on discordbots.org, or something went wrong.')
            res = await res.json()
            res = addict.Dict(res)
            widget = prepare(ROOT_URL, bot.id)
            title = f'<:dblCertified:392249976639455232> {res.username}' if res.certifiedBot else res.username
            memberparser = commands.MemberConverter()
            colour = 1030633 if res.certifiedBot else 35554
            owners = []
            for i in res.owners:
                try:
                    member = await memberparser.convert(ctx, i) # mfw i drop an await
                    owners.append(f'**{member.name}**#{member.discriminator} (`{member.id}`)')
                except commands.errors.BadArgument:
                    owners.append(f'`{i}`')
            embed = discord.Embed(title=title, description=res.shortDesc, colour=colour)
            embed.add_field(name='Lib', value=res.lib, inline=False)
            embed.add_field(name='Server Count', value=res.server_count, inline=False)
            embed.add_field(name='Owner' if len(owners) == 1 else 'Owners', value='\n'.join(owners), inline=False)
            embed.set_image(url=widget)
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(BotLists(bot))
