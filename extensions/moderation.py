# MODERATION FOR TUXEDO
# (c) ry000001 2017
# This code will *only* work on Tuxedo Discord bot.
# This code is highly private and confidential. Do not leak.
import discord
from discord.ext import commands
from discord import utils as dutils

chars = '!#/()=%&'

class Moderation:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def mute(self, ctx, member : discord.Member):
        """Mutes or unmutes a member"""
        if ctx.author == member:
            return await ctx.send('Why are you trying to mute yourself...?')
        if not ctx.author.permissions_in(ctx.channel).manage_roles:
            return await ctx.send(':no_entry_sign: Not enough permissions. You need Manage Roles.')
        if not ctx.me.permissions_in(ctx.channel).manage_roles:
            return await ctx.send(':no_entry_sign: Grant the bot Manage Roles before doing this.')
        for i in ctx.guild.text_channels:
            await i.set_permissions(member, send_messages=not member.permissions_in(i).send_messages)
        await ctx.send(':ok_hand:')

    @commands.command()
    async def ban(self, ctx, member : discord.Member, *, reason : str):
        """Bans a member. You can specify a reason."""
        if ctx.author == member:
            return await ctx.send('Don\'t ban yourself, please.')
        if not ctx.author.permissions_in(ctx.channel).ban_members:
            return await ctx.send(':no_entry_sign: Not enough permissions. You need Ban Members.')
        if not ctx.me.permissions_in(ctx.channel).ban_members:
            return await ctx.send(':no_entry_sign: Grant the bot Ban Members before doing this.')
        await ctx.guild.ban(member, reason=f'[{str(ctx.author)}] {reason}' if reason else f'Ban by {str(ctx.author)}', delete_message_days=7)
        await ctx.send(':ok_hand:')

    @commands.command()
    async def kick(self, ctx, member : discord.Member, *, reason : str):
        """Kicks a member. You can specify a reason."""
        if ctx.author == member:
            return await ctx.send('Don\'t kick yourself, please.')
        if not ctx.author.permissions_in(ctx.channel).kick_members:
            return await ctx.send(':no_entry_sign: Not enough permissions. You need Kick Members.')
        if not ctx.me.permissions_in(ctx.channel).kick_members:
            return await ctx.send(':no_entry_sign: Grant the bot Kick Members before doing this.')
        await ctx.guild.kick(member, reason=f'[{str(ctx.author)}] {reason}' if reason else f'Kick by {str(ctx.author)}')
        await ctx.send(':ok_hand:')
    

        

def setup(bot):
    bot.add_cog(Moderation(bot))