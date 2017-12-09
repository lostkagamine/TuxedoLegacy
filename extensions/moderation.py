# MODERATION FOR TUXEDO
# (c) ry000001 2017
# This code will *only* work on Tuxedo Discord bot.
# This code is free and open source software. Feel free to leak.
import discord
from discord.ext import commands
from discord import utils as dutils
from utils import switches
import asyncio
import random
import unidecode
import re
import rethinkdb as r
chars = '!#/()[]{}-=%&~._,;:^\'"+-`$'
dehoist_char = '𛲢' # special character, to be used for dehoisting

pingmods_disabled = [110373943822540800]

class Moderation:
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.conn
        self.rolebans = {}
        @bot.listen('on_member_update')
        async def on_member_update(before, after):
            g = after.guild
            isascii = lambda s: len(s) == len(s.encode())
            if after.display_name.startswith(tuple(chars)): # BEGIN AUTO DEHOIST MEME
                exists = (lambda: list(r.table('settings').filter(
                    lambda a: a['guild'] == str(g.id)).run(self.conn)) != [])()
                if not exists:
                    return
                settings = list(r.table('settings').filter(
                    lambda a: a['guild'] == str(g.id)).run(self.conn))[0]
                if 'auto_dehoist' in settings.keys():
                    if settings['auto_dehoist']:
                        await after.edit(nick=f'{dehoist_char}{after.display_name}', reason='[Automatic dehoist]')
            if isascii(after.display_name) == False and not after.display_name.startswith(dehoist_char):
                exists = (lambda: list(r.table('settings').filter(
                    lambda a: a['guild'] == str(g.id)).run(self.conn)) != [])()
                if not exists:
                    return
                settings = list(r.table('settings').filter(
                    lambda a: a['guild'] == str(g.id)).run(self.conn))[0]
                if 'auto_decancer' in settings.keys():
                    if settings['auto_decancer']:
                        aaa = unidecode.unidecode_expect_nonascii(after.display_name)
                        if len(aaa) > 32:
                            aaa = aaa[0:32-3] + '...'
                        await after.edit(nick=aaa, reason='[Automatic decancer]')
            if before.roles == after.roles:
                return
            if len(before.roles) < len(after.roles):
                return
            # they had a role removed from them
            if after.roles == [after.guild.default_role]:
                # no roles; should be after a manual untoss
                try:
                    if self.rolebans[after.id][after.guild.id] in [None, []]:
                        return # they weren't rolebanned
                    await after.edit(roles=self.rolebans[after.id][after.guild.id], reason='[Manual role restore]')
                    self.rolebans[after.id][after.guild.id] = None
                except KeyError or discord.Forbidden:
                    return

                

    def get_role(self, guild, id):
        for i in guild.roles:
            if i.id == id: return i
        return None

    @commands.command(aliases=['rb', 'toss'])
    async def roleban(self, ctx, member:discord.Member, *, reason:str=None):
        'Mutes a member. You can specify a reason.'
        g = ctx.guild
        perms = ctx.author.permissions_in(ctx.channel)
        perrms = member.permissions_in(ctx.channel)
        if perms.manage_roles or perms.kick_members or perms.ban_members:
            exists = (lambda: list(r.table('settings').filter(
                lambda a: a['guild'] == str(g.id)).run(self.conn)) != [])()
            if not exists:
                return
            # we know the guild has an entry in the settings
            if (perrms.manage_roles or perrms.kick_members or perrms.ban_members) or not ctx.author.top_role > member.top_role:
                await ctx.send(':x: You can\'t roleban a mod.')
                return
            settings = list(r.table('settings').filter(
                lambda a: a['guild'] == str(g.id)).run(self.conn))[0]
            channel = None
            if 'rolebanned_role' not in settings.keys():
                return await ctx.send(f':x: You haven\'t set up a rolebanned role. Please use `{ctx.prefix}set rolebanned_role <role name>`')
            if 'staff_channel' in settings.keys():
                channel = ctx.guild.get_channel(int(settings['staff_channel']))
            role = self.get_role(ctx.guild, int(settings['rolebanned_role']))
            try:
                meme = self.rolebans[member.id][ctx.guild.id]
                if meme != [] and meme != None or role in member.roles:
                    return await ctx.send(':x: This member is already rolebanned.')
            except KeyError:
                pass
            try:
                aa = self.rolebans[member.id]
                if aa == None:
                    self.rolebans[member.id] = {}
            except KeyError:
                self.rolebans[member.id] = {}
            self.rolebans[member.id][ctx.guild.id] = []
            try:
                for i in member.roles:
                    if i != g.default_role:
                        self.rolebans[member.id][ctx.guild.id].append(i)
                await member.edit(roles=[role], reason=f'[{str(ctx.author)}] {reason}' if reason != None else f'[Roleban by {str(ctx.author)}]')
                prevroles = ', '.join([i.name for i in self.rolebans[member.id][ctx.guild.id]])
                if prevroles == '': prevroles = 'None'
                await ctx.send(f'**{member.name}**#{member.discriminator} ({member.id}) has been rolebanned.\nPrevious roles: {prevroles}')
                if type(channel) == discord.TextChannel:
                    await channel.send(f'**{member.name}**#{member.discriminator} ({member.id}) has just been rolebanned in <#{ctx.channel.id}>.\nTheir previous roles were: {prevroles}')
            except discord.Forbidden:
                return await ctx.send(':x: I don\'t have permission to do this. Give me Manage Roles or move my role higher.')
        else:
            return await ctx.send(':no_entry_sign: Not enough permissions. You need either Manage Roles, Kick Members or Ban Members.')

    @commands.command(aliases=['urb', 'untoss'])
    async def unroleban(self, ctx, member:discord.Member, *, reason : str=None):
        'Unmutes a member. You can specify a reason.'
        g = ctx.guild
        perms = ctx.author.permissions_in(ctx.channel)
        if perms.manage_roles or perms.kick_members or perms.ban_members:
            exists = (lambda: list(r.table('settings').filter(
                lambda a: a['guild'] == str(g.id)).run(self.conn)) != [])()
            if not exists:
                return
            # we know the guild has an entry in the settings
            settings = list(r.table('settings').filter(
                lambda a: a['guild'] == str(g.id)).run(self.conn))[0]
            channel = None
            if 'rolebanned_role' not in settings.keys():
                return await ctx.send(f':x: You haven\'t set up a rolebanned role. Please use `{ctx.prefix}set rolebanned_role <role name>`')
            if 'staff_channel' in settings.keys():
                channel = ctx.guild.get_channel(int(settings['staff_channel']))
            role = self.get_role(ctx.guild, int(settings['rolebanned_role']))
            try:
                aa = self.rolebans[member.id]
                meme = self.rolebans[member.id][ctx.guild.id]
                if meme == None or meme == [] or role not in member.roles:
                    raise KeyError('is not moot, does not compute')
            except KeyError:
                return await ctx.send(':x: This member wasn\'t rolebanned.')
            try:
                roles = []
                for i in self.rolebans[member.id][ctx.guild.id]:
                    if i != g.default_role:
                        roles.append(i)
                if roles == []: return
                await member.edit(roles=roles)
                await member.remove_roles(role, reason=f'[{str(ctx.author)}] {reason}' if reason != None else f'[Unroleban by {str(ctx.author)}]')
                prevroles = ', '.join([i.name for i in roles])
                if prevroles == '': prevroles = 'None'
                self.rolebans[member.id][ctx.guild.id] = None
                await ctx.send(f'**{member.name}**#{member.discriminator} ({member.id}) has been unrolebanned.\nRoles restored: {prevroles}')
                if type(channel) == discord.TextChannel:
                    await channel.send(f'**{member.name}**#{member.discriminator} ({member.id}) has just been unrolebanned in <#{ctx.channel.id}>.\nThe roles restored are: {prevroles}')
            except discord.Forbidden:
                return await ctx.send(':x: I don\'t have permission to do this. Give me Manage Roles or move my role higher.')
        else:
            return await ctx.send(':no_entry_sign: Not enough permissions. You need either Manage Roles, Kick Members or Ban Members.')

    @commands.command()
    async def ban(self, ctx, member : discord.Member, *, reason : str = None):
        """Bans a member. You can specify a reason."""
        if ctx.author == member:
            return await ctx.send('Don\'t ban yourself, please.')
        if not ctx.author.permissions_in(ctx.channel).ban_members:
            return await ctx.send(':no_entry_sign: Not enough permissions. You need Ban Members.')
        if not ctx.me.permissions_in(ctx.channel).ban_members:
            return await ctx.send(':no_entry_sign: Grant the bot Ban Members before doing this.')
        if ctx.author.top_role <= member.top_role:
            return await ctx.send(':no_entry_sign: You can\'t ban someone with a higher role than you!')
        if ctx.me.top_role <= member.top_role:
            return await ctx.send(':no_entry_sign: I can\'t ban someone with a higher role than me!')
        await ctx.guild.ban(member, reason=f'[{str(ctx.author)}] {reason}' if reason else f'Ban by {str(ctx.author)}', delete_message_days=7)
        msg = await ctx.send(':ok_hand:')
        await asyncio.sleep(3)
        await msg.delete()

    @commands.command()
    async def kick(self, ctx, member : discord.Member, *, reason : str = None):
        """Kicks a member. You can specify a reason."""
        if ctx.author == member:
            return await ctx.send('Don\'t kick yourself, please.')
        if not ctx.author.permissions_in(ctx.channel).kick_members:
            return await ctx.send(':no_entry_sign: Not enough permissions. You need Kick Members.')
        if not ctx.me.permissions_in(ctx.channel).kick_members:
            return await ctx.send(':no_entry_sign: Grant the bot Kick Members before doing this.')
        if ctx.author.top_role <= member.top_role:
            return await ctx.send(':no_entry_sign: You can\'t kick someone with a higher role than you!')
        if ctx.me.top_role <= member.top_role:
            return await ctx.send(':no_entry_sign: I can\'t kick someone with a higher role than me!')
        await ctx.guild.kick(member, reason=f'[{str(ctx.author)}] {reason}' if reason else f'Kick by {str(ctx.author)}')
        msg = await ctx.send(':ok_hand:')
        await asyncio.sleep(3)
        await msg.delete()

    @commands.command()
    async def dehoist(self, ctx, member : discord.Member, *, flags : str = None):
        'Remove a hoisting member\'s hoist.'
        if not ctx.author.permissions_in(ctx.channel).manage_nicknames:
            return await ctx.send(':no_entry_sign: Not enough permissions. You need Manage Nicknames.')
        if not ctx.me.permissions_in(ctx.channel).manage_nicknames:
            return await ctx.send(':no_entry_sign: Grant the bot Manage Nicknames before doing this.')
        if ctx.author.top_role <= member.top_role or ctx.me.top_role <= member.top_role:
            return await ctx.send(':no_entry_sign: I can\'t dehoist a member with a higher role than you, and you can\'t dehoist someone with a higher role than you.')
        if ctx.author == member:
            return await ctx.send('Nope, can\'t do this.')
        name = member.nick if member.nick else member.name
        try:
            await member.edit(nick=f'{dehoist_char}{name}')
        except discord.Forbidden:
            await ctx.send('Oops. I can\'t dehoist this member because my privilege is too low. Move my role higher.')
        else:
            await ctx.send(':ok_hand:')

    def cleanformat(self, number):
        string = ""
        if number == 1:
            string = "deleted 1 message"
        if number == 0:
            string = "deleted no messages"
        else:
            string = "deleted {} messages".format(number)
        return "Bot cleanup successful, {} (Method A)".format(string)

    def pruneformat(self, number):
        string = ""
        if number == 1:
            string = "Deleted 1 message"
        if number == 0:
            string = "Deleted no messages"
        else:
            string = "Deleted {} messages".format(number)
        return string

    @commands.command(description="Clean up the bot's messages.")
    async def clean(self, ctx, amount : int=50):
        """Clean up the bot's messages."""
        if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            delet = await ctx.channel.purge(limit=amount+1, check=lambda a: a.author == self.bot.user, bulk=True)
            eee = await ctx.send(self.cleanformat(len(delet)))
            await asyncio.sleep(3)
            return await eee.delete()
        else:
            async for i in ctx.channel.history(limit=amount): # bugg-o
                if i.author == self.bot.user:
                    await i.delete()
            
            uwu = await ctx.send("Bot cleanup successful (Method B)")
            await asyncio.sleep(3)
            return await uwu.delete()

    @commands.command(description="Purge messages in the channel.", aliases=["prune"])
    async def purge(self, ctx, amount : int=50, *flags):
        if not ctx.author.permissions_in(ctx.channel).manage_messages:
            return await ctx.send(":x: Not enough permissions.")

        if not ctx.me.permissions_in(ctx.channel).manage_messages:
            return await ctx.send(":x: I don't have enough permissions.")
        
        meme = switches.parse(' '.join(flags))
        bots = (lambda: 'bots' in meme[0].keys())()

        if not bots:
            await ctx.message.delete()

        delet = await ctx.channel.purge(limit=amount, check=lambda a: a.author.bot if bots else True, bulk=True) # why is it bugged  
        eee = await ctx.send(self.pruneformat(len(delet)))
        await asyncio.sleep(3)
        return await eee.delete()

    @commands.command(description="Ban a user, even when not in the server.", aliases=['shadowban', 'hban'])
    async def hackban(self, ctx, user : int, *, reason : str = None):
        'Ban someone, even when not in the server.'
        if not ctx.author.permissions_in(ctx.channel).ban_members:
            return await ctx.send(':no_entry_sign: Not enough permissions. You need Ban Members.')
        if not ctx.me.permissions_in(ctx.channel).ban_members:
            return await ctx.send(':no_entry_sign: Grant the bot Ban Members before doing this.')
        await ctx.bot.http.ban(user, ctx.guild.id, 7, reason=f'[{str(ctx.author)}] {reason}' if reason else f'Hackban by {str(ctx.author)}')
        msg = await ctx.send(':ok_hand:')
        await asyncio.sleep(3)
        await msg.delete()

    @commands.command(description='Ping an online moderator.', aliases=['pingmod'])
    async def pingmods(self, ctx, *, reason : str = None):
        'Ping an online moderator.'
        if ctx.guild.id in pingmods_disabled:
            return await ctx.send(':x: This feature isn\'t available here.')
        mods = [i for i in ctx.guild.members if (i.permissions_in(ctx.channel).kick_members or i.permissions_in(ctx.channel).ban_members) and
                                                not i.bot and
                                                (i.status == discord.Status.online or i.status == 'online')]
        mod = random.choice(mods)
        reasonless_string = f'Mod Autoping: <@{mod.id}> (by **{ctx.author.name}**#{ctx.author.discriminator})'
        reason_string = f'Mod Autoping:\n**{reason}**\n<@{mod.id}> (by **{ctx.author.name}**#{ctx.author.discriminator})'
        await ctx.send(reason_string if reason != None else reasonless_string)

    @commands.command(description='Decancer a member.')
    async def decancer(self, ctx, member : discord.Member):
        '"Decancer" a member, or strip all the non-ASCII characters from their name. Useful to make your chat look good.'
        if ctx.me.permissions_in(ctx.channel).manage_nicknames and ctx.author.permissions_in(ctx.channel).manage_nicknames:
            cancer = member.display_name
            decancer = unidecode.unidecode_expect_nonascii(cancer)
            # decancer = re.sub(r'\D\W', '', decancer)
            if len(decancer) > 32:
                decancer = decancer[0:32-3] + "..."
            try:
                await member.edit(nick=decancer)
                await ctx.send(f'Successfully decancered {cancer} to ​`{decancer}​`.')
            except discord.Forbidden:
                await ctx.send('I couldn\'t decancer this member. Please move my role higher.')
        else:
            cancer = member.display_name
            decancer = unidecode.unidecode_expect_nonascii(cancer)
            await ctx.send(f'The decancered version of {cancer} is ​`{decancer}​`.')

    @commands.command(description='View online mods.')
    async def mods(self, ctx):
        'View online mods.'
        online = []
        offline = []
        idle = []
        dnd = []
        icons = {'online': '<:online:313956277808005120>', 'offline': '<:offline:313956277237710868>', 'idle': '<:away:313956277220802560>', 'dnd': '<:dnd:313956276893646850>',
                 'invis': '<:invisible:313956277107556352>'} # dbots icons
        mods = [i for i in ctx.guild.members if not i.bot and (i.permissions_in(ctx.channel).kick_members or i.permissions_in(ctx.channel).ban_members)]
        for i in mods: # HIGHLIGHT-PROOF (tm) TECHNOLOGY
            if i.status == discord.Status.online: online.append(f'**{i.name[0:1]}\u200b{i.name[1:len(i.name)]}**#{i.discriminator}')
            if i.status == discord.Status.offline: offline.append(f'**{i.name[0:1]}\u200b{i.name[1:len(i.name)]}**#{i.discriminator}')
            if i.status == discord.Status.idle: idle.append(f'**{i.name[0:1]}\u200b{i.name[1:len(i.name)]}**#{i.discriminator}')
            if i.status == discord.Status.dnd: dnd.append(f'**{i.name[0:1]}\u200b{i.name[1:len(i.name)]}**#{i.discriminator}')

        msg = f'''
**Moderators in {ctx.guild}**:
{icons['online']} **Online:** {' | '.join(online) if online != [] else 'None'}
{icons['idle']} **Away:** {' | '.join(idle) if idle != [] else 'None'}
{icons['dnd']} **DnD:** {' | '.join(dnd) if dnd != [] else 'None'}
{icons['offline']} **Offline:** {' | '.join(offline) if offline != [] else 'None'}
'''
        await ctx.send(msg)
        
        
def setup(bot):
    bot.add_cog(Moderation(bot))
