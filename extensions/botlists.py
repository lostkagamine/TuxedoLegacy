import discord 
from discord.ext import commands

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

def setup(bot):
    bot.add_cog(BotLists(bot))
