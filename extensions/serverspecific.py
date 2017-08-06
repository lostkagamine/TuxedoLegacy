import discord
from discord import utils
from discord.ext import commands

bannerole = [343465828282269696, 343477848540971010]

class ServerSpecific:

    def __init__(self, bot):
        self.bot = bot

    def checkShare(self, a, b):
        return any(x in a for x in b) # copied from stack ofc

    def findShared(self, a, b):
        for x in a:
            for y in b:
                if x == y:
                    return x
        return False

    @commands.command()
    async def mute(self, ctx, target : discord.Member):
        perms = ctx.author.permissions_in(ctx.channel).manage_roles
        if not perms.manage_roles or not perms.ban_members:
            return await ctx.send(":x: Not enough permissions.")
        if not self.checkShare([i.id for i in ctx.guild.roles], bannerole):
            await ctx.send(":x: This isn't the right guild.")
            return
        
        mootid = self.findShared([i.id for i in ctx.guild.roles], bannerole)
        # print(mootid)
        moot = await commands.RoleConverter().convert(ctx, str(mootid))
        await target.add_roles(moot)
        await ctx.send(f"**{target.name}#{target.discriminator} has been muted.**\n\nThey have been sent to a special channel that only muted users or staff can access.")

    


def setup(bot):
    bot.add_cog(ServerSpecific(bot))
