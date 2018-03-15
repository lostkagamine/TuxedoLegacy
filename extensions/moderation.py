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
import time
import rethinkdb as r
import isodate
from utils import argparse
import datetime
chars = ("!", "\"", "#", "$", "%", "&", "'", "(", ")", "*", "+", ",", "-", ".", "/", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ":", ";", "<", "=", ">", "?", "@", "[", "\\", "]", "^", "_", "`")
# to the above char tuple: thanks road
dehoist_char = '𛲢' # special character, to be used for dehoisting

badargs = [
    'Oh, what are "arguments"? Whatever those are, you gotta fix them.',
    'Bad arguments! Whatever those are...',
    'What\'s an argument? ...Okay, it doesn\'t really matter because you need to fix them.'
]

pingmods_disabled = [110373943822540800]

class Moderation:

    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.conn
        self.rolebans = {}
        self.task = bot.loop.create_task(self.loop())
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
                        try:
                            await after.edit(nick=f'{dehoist_char}{after.display_name[0:31]}', reason='[Automatic dehoist]')
                        except discord.Forbidden:
                            return
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
                        try:
                            await after.edit(nick=aaa, reason='[Automatic decancer]')
                        except discord.Forbidden:
                            return
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

    def __unload(self):
        self.task.cancel()

    async def get_user(self, uid: int):
        user = None  # database fetch
        if user is not None:
            # noinspection PyProtectedMember
            return discord.User(state=self.bot._connection, data=user)  # I'm sorry Danny

        user = self.bot.get_user(uid)
        if user is not None:
            return user

        try:
            user = await self.bot.get_user_info(uid)
        except discord.NotFound:
            user = None
        if user is not None:  # intentionally leaving this at the end so we can add more methods after this one
            return user
        
    async def loop(self):
        while True:
            await asyncio.sleep(60) # check bans every minute
            tbl = r.table('tempbans').run(self.conn)
            tbl = [i for i in tbl]
            for i in tbl: # syntax: {'guild': guild ID, 'moderator': mod ID, 'user': user ID, 'timestamp': original timestamp, 'expiration': when it expires}
                if float(i['expiration']) <= datetime.datetime.utcnow().timestamp():
                    mod = await self.get_user(int(i['moderator']))
                    user = await self.get_user(int(i['user'])) # LOL PARENTHESES
                    try:
                        await self.bot.get_guild(int(i['guild'])).unban(user, reason=f'[Automatic: ban placed by {mod} expired]') # LOL PARENTHESES V2
                    except discord.Forbidden:
                        try:
                            hecc = datetime.datetime.fromtimestamp(float(i['timestamp']))
                            await mod.send(f'''
Oh! It appears your ban for {user} has expired, but I couldn't unban them automatically!
Please unban them! Their ban has expired on {hecc}.
                            ''')
                        except discord.Forbidden:
                            continue # can't dm, give up
                        continue 
                    except discord.HTTPException: # will test tomorrow, bleh
                        continue     
                r.table('tempbans').filter({'guild': i['guild'], 'user': i['user']}).delete().run(self.conn)


    def get_role(self, guild, id):
        for i in guild.roles:
            if i.id == id: return i
        return None

    @commands.command(aliases=['m'])
    async def mute(self, ctx, *args):
        """Mutes a user"""
        nosetting = f':x: The muted role list isn\'t set! Set it with `{ctx.prefix}set muted_roles \'Role 1\' \'Role 2\' \'Role 3\'`. You can have an infinite amount of roles in the list.'
        badsetting = f':x: The muted role list is incomplete! Please re-run setup with `{ctx.prefix}set muted_roles \'Role 1\' \'Role 2\' \'Role 3\'`. You can have an infinite amount of roles in the list.'
        parser = argparse.DiscordFriendlyArgparse(prog=ctx.invoked_with, add_help=True)
        parser.add_argument('-u', '--users', nargs='+', required=True, metavar='@user', help='List of users to mute.')
        parser.add_argument('-t', '--tier', metavar='tier', type=int, help='Tier number for the type of mute.')
        parser.add_argument('-r', '--reason', metavar='reason', help='The reason for the mute.')
        parser.add_argument('-s', '--strip', action='store_true', help='Brings back old roleban behaviour.')
        try:
            args = parser.parse_args(args)
        except argparse.DiscordArgparseError or argparse.DiscordArgparseMessage as e:
            return await ctx.send(random.choice(badargs) + '\n' + str(e))
        tier = args.tier if args.tier != None else 0
        g = ctx.guild
        exists = (lambda: list(r.table('settings').filter(
            lambda a: a['guild'] == str(g.id)).run(self.conn)) != [])()
        if not exists:
            return await ctx.send(nosetting)
        settings = list(r.table('settings').filter(
            lambda a: a['guild'] == str(g.id)).run(self.conn))[0]
        if 'muted_roles' not in settings.keys():
            return await ctx.send(nosetting)
        def get_role(g, id):
            for i in g.roles:
                if i.id == id:
                    return i
            return None
        roles = [get_role(g, int(i)) for i in settings['muted_roles']]
        if any(i == None for i in roles):
            return await ctx.send(badsetting) #shouldn't happen
        if tier > len(roles) or tier < 0:
            return await ctx.send(f':x: The tier value must range between 0 and {len(roles)}.')
        if not ctx.author.permissions_in(ctx.channel).kick_members or not ctx.author.permissions_in(ctx.channel).manage_roles or not ctx.author.permissions_in(ctx.channel).ban_members:
            return await ctx.send(':no_entry_sign: Not enough permissions. You need Manage Roles, Kick Members or Ban Members.')
        if not ctx.me.permissions_in(ctx.channel).manage_roles:
            return await ctx.send(':no_entry_sign: I don\'t have enough permissions. Give me Manage Roles.')
        people = []
        for i in args.users:
            try:
                m = await commands.MemberConverter().convert(ctx, i)
            except commands.errors.BadArgument as e:
                return await ctx.send(f':x: | {e}')
            people.append(m)
        if any(ctx.author.top_role <= i.top_role for i in people):
            return await ctx.send(':x: You cannot mute someone with an equal or greater top role.')
        if any(ctx.me.top_role <= i.top_role for i in people):
            return await ctx.send(':x: I cannot mute someone with a higher top role than me. Move my role up.')
        for i in people:
            for x in i.roles:
                if x in roles:
                    return await ctx.send(':x: One or more people are already muted.')
        for i in people:
            if args.strip is not None:
                try:
                    self.rolebans[i.id][ctx.guild.id] = i.roles
                    await i.edit(roles=[roles[tier]], reason=f'[{ctx.author}] {args.reason}' if args.reason != None else f'Mute by {ctx.author}')
                except KeyError:
                    pass
            await i.add_roles(roles[tier], reason=f'[{ctx.author}] {args.reason}' if args.reason != None else f'Mute by {ctx.author}')
        await ctx.send(f':ok_hand: {", ".join([f"**{i.name}**#{i.discriminator}" for i in people])} {"has" if len(people) == 1 else "have"} been muted with tier **{tier}**, which is role {roles[tier]}.')

    @commands.command(aliases=['um'])
    async def unmute(self, ctx, *args):
        """Unmutes a user"""
        nosetting = f':x: The muted role list isn\'t set! Set it with `{ctx.prefix}set muted_roles \'Role 1\' \'Role 2\' \'Role 3\'`. You can have an infinite amount of roles in the list.'
        badsetting = f':x: The muted role list is incomplete! Please re-run setup with `{ctx.prefix}set muted_roles \'Role 1\' \'Role 2\' \'Role 3\'`. You can have an infinite amount of roles in the list.'
        parser = argparse.DiscordFriendlyArgparse(prog=ctx.invoked_with, add_help=True)
        parser.add_argument('-u', '--users', nargs='+', required=True, metavar='@user', help='List of users to unmute.')
        parser.add_argument('-r', '--reason', metavar='reason', help='The reason for the unmute.')
        try:
            args = parser.parse_args(args)
        except argparse.DiscordArgparseError or argparse.DiscordArgparseMessage as e:
            return await ctx.send(random.choice(badargs) + '\n' + str(e))
        g = ctx.guild
        exists = (lambda: list(r.table('settings').filter(
            lambda a: a['guild'] == str(g.id)).run(self.conn)) != [])()
        if not exists:
            return await ctx.send(nosetting)
        settings = list(r.table('settings').filter(
            lambda a: a['guild'] == str(g.id)).run(self.conn))[0]
        if 'muted_roles' not in settings.keys():
            return await ctx.send(nosetting)
        def get_role(g, id):
            for i in g.roles:
                if i.id == id:
                    return i
            return None
        roles = [get_role(g, int(i)) for i in settings['muted_roles']]
        if any(i == None for i in roles):
            return await ctx.send(badsetting) #shouldn't happen
        if not ctx.author.permissions_in(ctx.channel).kick_members or not ctx.author.permissions_in(ctx.channel).manage_roles or not ctx.author.permissions_in(ctx.channel).ban_members:
            return await ctx.send(':no_entry_sign: Not enough permissions. You need Manage Roles, Kick Members or Ban Members.')
        if not ctx.me.permissions_in(ctx.channel).manage_roles:
            return await ctx.send(':no_entry_sign: I don\'t have enough permissions. Give me Manage Roles.')
        people = []
        for i in args.users:
            try:
                m = await commands.MemberConverter().convert(ctx, i)
            except commands.errors.BadArgument as e:
                return await ctx.send(f':x: | {e}')
            people.append(m)
        if any(ctx.author.top_role <= i.top_role for i in people):
            return await ctx.send(':x: You cannot unmute someone with an equal or greater top role.')
        if any(ctx.me.top_role <= i.top_role for i in people):
            return await ctx.send(':x: I cannot unmute someone with a higher top role than me. Move my role up.')
        any_in = lambda a, b: any(i in b for i in a)
        a = {}
        for i in people:
            a[i.id] = [v for v in i.roles if v in set(roles)]
        if any(all(i == None for i in x) for x in a.values()):
            return await ctx.send(':x: One or more people were not muted.')
        for person in people:
            try:
                if self.rolebans[i.id][ctx.guild.id] is not None:
                    await person.edit(roles=self.rolebans[i.id][ctx.guild.id], reason=f'[{ctx.author}] {args.reason}' if args.reason != None else f'Unmute by {ctx.author}')
                    self.rolebans[i.id][ctx.guild.id] = None
            except KeyError:
                pass
            await person.remove_roles(*a[person.id], reason=f'[{ctx.author}] {args.reason}' if args.reason != None else f'Unmute by {ctx.author}')
        await ctx.send(f':ok_hand: {", ".join([f"**{i.name}**#{i.discriminator}" for i in people])} {"has" if len(people) == 1 else "have"} been unmuted.')

    @commands.command(aliases=['b'])
    async def ban(self, ctx, *args):
        """Bans a member"""
        parser = argparse.DiscordFriendlyArgparse(prog=ctx.command.name, add_help=True)
        parser.add_argument('-u', '--users', nargs='+', metavar='@user', required=True, help='List of users to ban.')
        parser.add_argument('-r', '--reason', metavar='Reason', help='A reason for the ban.')
        parser.add_argument('-t', '--time', metavar='Time', 
                            help='A time for temporary bans. Once this is up, the ban will expire and the person will be unbanned. Must be formatted in ISO 8601. Omit for permanent ban.')
        parser.add_argument('-d', '--days', metavar='Delete days', type=int, help='How many days\' worth of messages to delete from the banned user.')
        try:
            args = parser.parse_args(args)
        except argparse.DiscordArgparseError as e:
            return await ctx.send(random.choice(badargs) + '\n' + str(e))
        people = []
        for i in args.users:
            try:
                member = await commands.MemberConverter().convert(ctx, i)
            except commands.errors.BadArgument as e:
                return await ctx.send(f':x: | {e}')
            if member == ctx.guild.me:
                return await ctx.send('You can\'t ban me with myself. That\'s not how it works.')
            if ctx.author == member:
                return await ctx.send('Don\'t ban yourself, please.')
            if not ctx.author.permissions_in(ctx.channel).ban_members:
                return await ctx.send(':no_entry_sign: Not enough permissions. You need Ban Members.')
            if not ctx.me.permissions_in(ctx.channel).ban_members:
                return await ctx.send(':no_entry_sign: I can\'t ban without Ban Members... Please give me that permission before doing this.')
            if ctx.author.top_role <= member.top_role:
                return await ctx.send(':no_entry_sign: You can\'t ban someone with a higher role than you!')
            if ctx.me.top_role <= member.top_role:
                return await ctx.send(':no_entry_sign: I can\'t ban someone with a higher role than me!')
            people.append(member)
        if args.time != None:
            for i in people:            
                try:
                    dura = isodate.parse_duration(args.time)
                except isodate.ISO8601Error as e:
                    return await ctx.send(f':x: | {e}')
                if type(dura) == isodate.Duration:
                    dura = dura.totimedelta() # make it super-safe
                expire = (dura + datetime.datetime.utcnow()).timestamp()
                now = datetime.datetime.utcnow().timestamp()
                r.table('tempbans').insert({
                    'moderator': str(ctx.author.id),
                    'user': str(i.id),
                    'timestamp': str(now),
                    'expiration': str(expire),
                    'guild': str(ctx.guild.id)
                }).run(self.bot.conn)
        for member in people:
            await ctx.guild.ban(member, reason=f'[{str(ctx.author)}] {args.reason}' if args.reason != None else f'Ban by {str(ctx.author)}', delete_message_days=args.days if args.days != None else 7)
        msg = await ctx.send(':hammer: The ban hammer has been swung!')
        await asyncio.sleep(3)
        await msg.delete()

    @commands.command(aliases=['uban', 'ub'])
    async def unban(self, ctx, *args):
        """Unbans a user"""
        parser = argparse.DiscordFriendlyArgparse(prog=ctx.command.name, add_help=True)
        parser.add_argument('-u', '--users', nargs='+', metavar='<id>', required=True, help='List of users to unban.')
        parser.add_argument('-r', '--reason', metavar='Reason', help='A reason for the unban.')
        try:
            args = parser.parse_args(args)
        except argparse.DiscordArgparseError as e:
            return await ctx.send(random.choice(badargs) + '\n' + str(e))
        for i in args.users:
            if not ctx.author.permissions_in(ctx.channel).ban_members:
                return await ctx.send(':no_entry_sign: Not enough permissions. You need Ban Members.')
            if not ctx.me.permissions_in(ctx.channel).ban_members:
                return await ctx.send(':no_entry_sign: I can\'t unban without Ban Members... Please give me that permission before doing this.')
            await ctx.guild.unban(await self.get_user(i), reason=f'[{str(ctx.author)}] {args.reason}' if args.reason != None else f'Unban by {str(ctx.author)}')
        await ctx.send('Okay, unbanned.', delete_after=3)

    @commands.command(aliases=['k'])
    async def kick(self, ctx, *args):
        """Kicks a member"""
        parser = argparse.DiscordFriendlyArgparse(prog=ctx.command.name, add_help=True)
        parser.add_argument('-u', '--users', nargs='+', metavar='@user', required=True, help='List of users to kick.')
        parser.add_argument('-r', '--reason', metavar='Reason', help='A reason for the kick.')
        try:
            args = parser.parse_args(args)
        except argparse.DiscordArgparseError as e:
            return await ctx.send(random.choice(badargs) + '\n' + str(e))
        members = []
        for i in args.users:
            try:
                member = await commands.MemberConverter().convert(ctx, i)
            except commands.errors.BadArgument as e:
                return await ctx.send(f':x: | {e}')
            if member == ctx.guild.me:
                return await ctx.send('You can\'t kick me with myself. That\'s not how it works.')
            if ctx.author == member:
                return await ctx.send('Don\'t kick yourself, please.')
            if not ctx.author.permissions_in(ctx.channel).kick_members:
                return await ctx.send(':no_entry_sign: Not enough permissions. You need Kick Members.')
            if not ctx.me.permissions_in(ctx.channel).kick_members:
                return await ctx.send(':no_entry_sign: I can\'t kick without Kick Members... Please give me that permission before doing this.')
            if ctx.author.top_role <= member.top_role:
                return await ctx.send(':no_entry_sign: You can\'t kick someone with a higher role than you!')
            if ctx.me.top_role <= member.top_role:
                return await ctx.send(':no_entry_sign: I can\'t kick someone with a higher role than me!')
            members.append(member)
        for i in members:
            await ctx.guild.kick(i, reason=f'[{str(ctx.author)}] {args.reason}' if args.reason else f'Kick by {str(ctx.author)}')
        msg = await ctx.send('Okay, kicked.')
        await asyncio.sleep(3)
        await msg.delete()

    @commands.command(aliases=['dh'])
    async def dehoist(self, ctx, member : discord.Member, *, flags : str = None):
        """Removes a hoisting user's hoist"""
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
            await ctx.send('M-Move my role higher!')
        else:
            await ctx.send('Okay, done.')

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
        """Clean up the bot's messages"""
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

    @commands.has_permissions(manage_messages=True)
    @commands.command(no_pm=True)
    async def purge(self, ctx, msgs: int, *, txt=None):
        """Purge last n messages or even messages with specified words"""
        await ctx.message.delete()
        if msgs < 10000:
            async for message in ctx.message.channel.history(limit=msgs):
                try:
                    if txt:
                        if txt.lower() in message.content.lower():
                            await message.delete()
                    else:
                        await message.delete()
                except:
                    pass
        else:
            await ctx.send('Too many messages to delete. Enter a number < 10000')

    @commands.command(description="Ban a user, even when not in the server.", aliases=['shadowban', 'hban'])
    async def hackban(self, ctx, user : int, *, reason : str = None):
        """Ban an ID"""
        if not ctx.author.permissions_in(ctx.channel).ban_members:
            return await ctx.send(':no_entry_sign: Not enough permissions. You need Ban Members.')
        if not ctx.me.permissions_in(ctx.channel).ban_members:
            return await ctx.send(':no_entry_sign: Grant the bot Ban Members before doing this.')
        await ctx.bot.http.ban(user, ctx.guild.id, 7, reason=f'[{str(ctx.author)}] {reason}' if reason else f'Hackban by {str(ctx.author)}')
        msg = await ctx.send(':hammer: The ban hammer has been swung!')
        await asyncio.sleep(3)
        await msg.delete()

    @commands.command(description='Ping an online moderator.', aliases=['pingmod'])
    async def pingmods(self, ctx, *, reason : str = None):
        """Ping an online staff member"""
        if ctx.guild.id in pingmods_disabled:
            return await ctx.send(':x: This feature isn\'t available here.')
        mods = [i for i in ctx.guild.members if (i.permissions_in(ctx.channel).kick_members or i.permissions_in(ctx.channel).ban_members or i.permissions_in(ctx.channel).manage_roles) and
                                                not i.bot and
                                                (i.status == discord.Status.online or i.status == 'online')]
        if mods == []:
            return await ctx.send(':x: No online mods available!')
        mod = random.choice(mods)
        reasonless_string = f'Mod Autoping: <@{mod.id}> (by **{ctx.author.name}**#{ctx.author.discriminator})'
        reason_string = f'Mod Autoping:\n**{reason}**\n<@{mod.id}> (by **{ctx.author.name}**#{ctx.author.discriminator})'
        await ctx.send(reason_string if reason != None else reasonless_string)

    @commands.command(description='Ping an online helper in Discord Bots.', aliases=['pinghelper'], hidden=True)
    async def pinghelpers(self, ctx, *, reason : str = None):
        """Ping an online helper in the Discord Bots server."""
        if ctx.guild.id != 110373943822540800:
            return
        mods = [i for i in ctx.guild.members if not i.bot and
                407326634819977217 in [r.id for r in i.roles] and
                (i.status == discord.Status.online or i.status == 'online')]
        if mods == []:
            return await ctx.send(':x: No online helpers available! You may want to ping a moderator.')
        mod = random.choice(mods)
        reasonless_string = f'Helper Autoping: <@{mod.id}> (by **{ctx.author.name}**#{ctx.author.discriminator})'
        reason_string = f'Helper Autoping:\n**{reason}**\n<@{mod.id}> (by **{ctx.author.name}**#{ctx.author.discriminator})'
        await ctx.send(reason_string if reason != None else reasonless_string);

    @commands.command(description='View online helpers in Discord Bots.')
    async def helpers(self, ctx):
        """View online helpers in the Discord Bots server."""
        if ctx.guild.id != 110373943822540800:
            return
        online = []
        offline = []
        idle = []
        dnd = []
        icons = {'online': '<:online:313956277808005120>', 'offline': '<:offline:313956277237710868>',
                 'idle': '<:away:313956277220802560>', 'dnd': '<:dnd:313956276893646850>',
                 'invis': '<:invisible:313956277107556352>'}  # dbots icons
        helpers = [i for i in ctx.guild.members if not i.bot and
                407326634819977217 in [r.id for r in i.roles]]
        for i in helpers:  # HIGHLIGHT-PROOF (tm) TECHNOLOGY
            if i.status == discord.Status.online: online.append(
                f'**{i.name[0:1]}\u200b{i.name[1:len(i.name)]}**#{i.discriminator}')
            if i.status == discord.Status.offline: offline.append(
                f'**{i.name[0:1]}\u200b{i.name[1:len(i.name)]}**#{i.discriminator}')
            if i.status == discord.Status.idle: idle.append(
                f'**{i.name[0:1]}\u200b{i.name[1:len(i.name)]}**#{i.discriminator}')
            if i.status == discord.Status.dnd: dnd.append(
                f'**{i.name[0:1]}\u200b{i.name[1:len(i.name)]}**#{i.discriminator}')

        msg = f'''
**Helpers in {ctx.guild}**:
{icons['online']} **Online:** {' | '.join(online) if online != [] else 'None'}
{icons['idle']} **Away:** {' | '.join(idle) if idle != [] else 'None'}
{icons['dnd']} **DnD:** {' | '.join(dnd) if dnd != [] else 'None'}
{icons['offline']} **Offline:** {' | '.join(offline) if offline != [] else 'None'}
'''
        await ctx.send(msg)

    @commands.command(description='Decancer a member.')
    async def decancer(self, ctx, member : discord.Member):
        """"Decancer" a member, or strip all the non-ASCII characters from their name. Useful to make your chat look good."""
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
        """View online staff"""
        online = []
        offline = []
        idle = []
        dnd = []
        icons = {'online': '<:online:313956277808005120>', 'offline': '<:offline:313956277237710868>', 'idle': '<:away:313956277220802560>', 'dnd': '<:dnd:313956276893646850>',
                 'invis': '<:invisible:313956277107556352>'} # dbots icons
        mods = [i for i in ctx.guild.members if not i.bot and
                (i.permissions_in(ctx.channel).kick_members or i.permissions_in(ctx.channel).ban_members or i.permissions_in(ctx.channel).manage_roles)]
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

    @commands.command(aliases=['vck'])
    async def vckick(self, ctx, member:discord.Member):
        """Kicks a member out of VC"""
        if not member.voice or not member.voice.channel:
            return await ctx.send(':x: | This member is not in a voice channel.')
        i = ctx.author # memes
        if not (i.permissions_in(ctx.channel).kick_members or i.permissions_in(ctx.channel).ban_members or i.permissions_in(ctx.channel).manage_roles):
            return await ctx.send(':x: | You need Kick Members, Ban Members or Manage Roles.')
        channel = await ctx.guild.create_voice_channel(''.join([str(random.randrange(1,9)) for i in range(5)]), reason=f'Voice-kick by {ctx.author}')
        try:
            await member.move_to(channel, reason=f'Voice-kick by {ctx.author}')
            await channel.delete(reason=f'Voice-kick by {ctx.author}')
            await ctx.send(':ok_hand:')
        except discord.Forbidden:
            return await ctx.send(':x: | Give me Manage Channels and Move Members before doing this.')
        except discord.HTTPException as e:
            return await ctx.send(f':x: | An unknown error has occurred while doing this. Please report this to my owner, ry00001#3487.\n**Error info:**```{type(e).__name__}: {e}```')

    @commands.command(aliases=['ld'])
    async def lockdown(self, ctx, channel:discord.TextChannel=None):
        """Lock down a channel"""
        if not channel:
            channel = ctx.channel
        perms = ctx.author.permissions_in(ctx.channel)
        if not (perms.ban_members or perms.kick_members or perms.manage_roles or perms.manage_channels):
            return await ctx.send(':no_entry_sign: | Insufficient permissions. You need Ban Members, Kick Members, Manage Roles or Manage Channels.')
        try:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        except discord.Forbidden:
            await ctx.send(':x: | I don\'t have enough permissions. Give me Manage Channels.')
        await ctx.send(':lock: | Lockdown successful.')

    @commands.command(aliases=['uld'])
    async def unlockdown(self, ctx, channel:discord.TextChannel=None):
        """Unlocks a channel that was previously on lockdown"""
        if not channel:
            channel = ctx.channel
        perms = ctx.author.permissions_in(ctx.channel)
        if not (perms.ban_members or perms.kick_members or perms.manage_roles or perms.manage_channels):
            return await ctx.send(':no_entry_sign: | Insufficient permissions. You need Ban Members, Kick Members, Manage Roles or Manage Channels.')
        try:
            await channel.set_permissions(ctx.guild.default_role, overwrite=None)
        except discord.Forbidden:
            await ctx.send(':x: | I don\'t have enough permissions. Give me Manage Channels.')
        await ctx.send(':unlock: | Unlockdown successful.')
        
def setup(bot):
    bot.add_cog(Moderation(bot))
