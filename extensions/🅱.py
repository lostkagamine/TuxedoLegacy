import discord
from discord.ext import commands
from utils import permissions

class B:
    def __init__(self, bot):
        self.bot = bot
        # do absolutely nothing

    @commands.command(aliases=['🅱'])
    async def b(self, ctx, arg:str):
        return await ctx.send(arg.replace('b', '🅱'))

    @commands.command(hidden=True)
    @permissions.owner()
    async def machine(self, ctx, action:str):
        if action == '🅱roke':
            await ctx.send('yes it 🅱roke, ima reboot now bai')
            exit(1)

def setup(bot):
    bot.add_cog(B(bot))
