import discord
from discord.ext import commands
import shlex

class RoleManagement:
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(aliases=['addrole', 'ar'])
    async def addroles(self, ctx, *, args):
        'Adds roles in bulk.'
        members = []
        roles = []
        try:
            shlex.split(args)
        except Exception:
            return await ctx.send(':x: | Bad arguments!')
        for i in ctx.message.mentions:
            args = args.replace(f'<@{i.id}>', '')
            args = args.replace(f'<@!{i.id}>', '')
            members.append(i)
        if members == []:
            return await ctx.send(f'One or more members not found.\nExample usage: `{ctx.prefix}{ctx.invoked_with} @ry00001 Members \'Staff Team\'`')
        args = shlex.split(args)
        for i in args:
            r = discord.utils.get(ctx.guild.roles, name=i)
            if not r:
                return await ctx.send(f':x: | One or more roles not found. Use \', not ", for multi-word roles.\nMake sure the capitalisation is correct.\nExample usage: `{ctx.prefix}{ctx.invoked_with} @ry00001 Members \'Staff Team\'`')
            roles.append(r)
        for m in members:
            await m.add_roles(*roles, reason=f'[Roles added by {ctx.author}]')
        await ctx.send('Okay, added.')

    @commands.command(aliases=['removerole', 'rmroles', 'rmrole', 'rr', 'rmr'])
    async def removeroles(self, ctx, *, args):
        'Removes roles in bulk.'
        members = []
        roles = []
        try:
            shlex.split(args)
        except Exception:
            return await ctx.send(':x: | Bad arguments!')
        for i in ctx.message.mentions:
            args = args.replace(f'<@{i.id}>', '')
            args = args.replace(f'<@!{i.id}>', '')
            members.append(i)
        if members == []:
            return await ctx.send(f'One or more members not found.\nExample usage: `{ctx.prefix}{ctx.invoked_with} @ry00001 Members \'Staff Team\'`')
        args = shlex.split(args)
        for i in args:
            r = discord.utils.get(ctx.guild.roles, name=i)
            if not r:
                return await ctx.send(f':x: | One or more roles not found. Use \', not ", for multi-word roles.\nMake sure the capitalisation is correct.\nExample usage: `{ctx.prefix}{ctx.invoked_with} @ry00001 Members \'Staff Team\'`')
            roles.append(r)
        for m in members:
            await m.remove_roles(*roles, reason=f'[Roles removed by {ctx.author}]')
        await ctx.send('Okay, removed.')

def setup(bot):
    bot.add_cog(RoleManagement(bot))
