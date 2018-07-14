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
                    member = memberparser.convert(ctx, i)
                    owners.append(f'**{i.username}**#{i.discriminator} (`{i.id}`)')
                except commands.errors.BadArgument:
                    owners.append(f'`{i}`')
            embed = discord.Embed(title=title, description=res.shortDesc, colour=colour)
            embed.add_field('Lib', res.lib, False)
            embed.add_field('Server Count', res.server_count, False)
            embed.add_field('Owner' if len(owners) == 1 else 'Owners', owners.join('\n'), False)
            embed.set_image(widget)
            await ctx.send(embed)


def setup(bot):
    bot.add_cog(BotLists(bot))
