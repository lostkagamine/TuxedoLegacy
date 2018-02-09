import discord
from discord.ext import commands
import rethinkdb as r
from utils import database, argparse, randomness
from enum import Enum
import datetime
import aiohttp

# Warnings cog for Tuxedo
# (c) ry00001 2018

colours = [
    0x2C2F33, # Greyple, dark theme BG, no warnings
    0xFFFF00, # Yellow, warned but not kicked
    0xFFA500, # Orange, kicked but not autobanned
    0xFF0000  # Red, you have been autobanned
]

class Stages(Enum):
    NO_WARNINGS = 0
    WARNED = 1
    AUTO_KICK = 2
    AUTO_BAN = 3

# WARNING DB FORMAT
# {
#   'guild': <guild ID>,
#   'user': <user ID>,
#   'warns': ['r1', 'r2', 'r3']
# }
# simple right

class Warnings:
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.conn

    async def haste_upload(self, text):
        with aiohttp.ClientSession() as sesh:
            async with sesh.post("https://hastebin.com/documents/", data=text, headers={"Content-Type": "text/plain"}) as r:
                r = await r.json()
                return r['key']

    def _add_warning(self, ctx, user, reason, count=1):
        has_warning = False
        try:
            r.table('warnings').filter({'user': str(user.id), 'guild': str(ctx.guild.id)}).run(self.conn).next()
            has_warning = True
        except r.net.DefaultCursorEmpty:
            pass
        if has_warning:
            warns = self.get_warnings(user, ctx.guild)
            warns.append({'mod': str(ctx.author.id), 'reason': reason, 'weight': int(count)})
            r.table('warnings').filter({'user': str(user.id), 'guild': str(ctx.guild.id)}).update({'warns': warns}).run(self.conn) # do thing
            return True
        else:
            try:
                r.table('warnings').insert({
                    'guild': str(ctx.guild.id),
                    'user': str(user.id),
                    'warns': [{
                        'mod': str(ctx.author.id),
                        'reason': reason,
                        'weight': int(count)
                    }]
                }).run(self.conn)
                return True
            except Exception as e:
                return e

    def _calculate_total(self, object_):
        tot = 0
        for i in object_:
            print(i)
            tot += int(i['weight'])
        return tot

    def _remove_warnings(self, ctx, user, count=1):
        has_warning = False
        try:
            r.table('warnings').filter({'user': str(user.id), 'guild': str(ctx.guild.id)}).run(self.conn).next()
            has_warning = True
        except r.net.DefaultCursorEmpty:
            pass
        if has_warning:
            warns = self.get_warnings(user, ctx.guild)
            counter = int(count)
            while counter > 0:
                if len(warns) == 0:
                    break
                if len(warns) == 1:
                    latest = warns[0]
                else:
                    latest = warns[-0]
                if int(latest['weight']) <= int(counter):
                    warns.pop() # delet latest
                    continue
                warns[-0]['weight'] -= counter
                counter -= int(latest['weight'])
                # should sort it
            print(warns)
            r.table('warnings').filter({'user': str(user.id), 'guild': str(ctx.guild.id)}).update({'warns': warns}).run(self.conn) # meem
            return True
        else:
            return False

    def get_warnings(self, user, guild):
        try:
            w = r.table('warnings').filter({'user': str(user.id), 'guild': str(guild.id)}).run(self.conn).next() # meem
            return w['warns']
        except Exception:
            return None

    def _calculate_stage(self, count, auto_setup=False, auto_kick=5, auto_ban=10):
        if auto_setup:
            if count == 0: return Stages.NO_WARNINGS.value
            elif count < auto_kick: return Stages.WARNED.value
            elif count >= auto_kick and count < auto_ban: return Stages.AUTO_KICK.value
            elif count >= auto_ban: return Stages.AUTO_BAN.value
        else:
            if count == 0: return Stages.NO_WARNINGS.value
            elif count <= 3: return Stages.WARNED.value
            elif count > 3 and count < 5: return Stages.AUTO_KICK.value
            elif count >= 5: return Stages.AUTO_BAN.value

    async def _send_warn_embed(self, ctx, users:list, reason, count):
        chan = database.check_setting(self.conn, ctx.guild, 'modlog_channel') # check guild
        if not chan:
            return # oooops
        e = discord.Embed()
        e.title = f'Warning Added'
        mm = ', '.join([f'{str(u)} ({count})' for u in users])
        e.add_field(name='Users', value=mm, inline=False)
        e.add_field(name='Reason', value=reason, inline=False)
        warns = {}
        for i in users:
            warns[i.id] = self.get_warnings(i, ctx.guild) # will exist
        print(warns)
        e.add_field(name='Current Warnings', value='\n'.join([f'{i}: {self._calculate_total(warns[i.id])}' for i in users]), inline=False)
        e.colour = colours[self._calculate_stage(
            self._calculate_total(
                list(warns.values())[0]
            )
        )]
        e.set_author(name=ctx.author, icon_url=ctx.author.avatar_url_as())
        e.timestamp = datetime.datetime.utcnow()
        await ctx.guild.get_channel(int(chan)).send(embed=e)

    async def _send_pardon_embed(self, ctx, users:list, reason, count):
        chan = database.check_setting(self.conn, ctx.guild, 'modlog_channel') # check guild
        if not chan:
            return # oooops
        e = discord.Embed()
        e.title = f'Warning Removed'
        mm = ', '.join([f'{str(u)} ({count})' for u in users])
        e.add_field(name='Users', value=mm, inline=False)
        e.add_field(name='Reason', value=reason, inline=False)
        warns = {}
        for i in users:
            warns[i.id] = self.get_warnings(i, ctx.guild) # will exist
        e.add_field(name='Current Warnings', value='\n'.join([f'{i}: {self._calculate_total(warns[i.id])}' for i in users]), inline=False)
        e.colour = 0x3dfc00
        e.set_author(name=ctx.author, icon_url=ctx.author.avatar_url_as())
        e.timestamp = datetime.datetime.utcnow()
        await ctx.guild.get_channel(int(chan)).send(embed=e)

    @commands.command(aliases=['w'])
    async def warn(self, ctx, *args):
        """Warns a user"""
        selfperms = ctx.author.permissions_in(ctx.channel)
        hasperm = (
            selfperms.kick_members or
            selfperms.ban_members or
            selfperms.manage_roles
        )
        if not hasperm:
            return await ctx.send(':no_entry_sign: Invalid permissions.')
        parser = argparse.DiscordFriendlyArgparse(prog=ctx.invoked_with, add_help=True)
        parser.add_argument('-u', '--users', nargs='+', required=True, metavar='@user', help='List of users to warn.')
        parser.add_argument('-r', '--reason', required=True, metavar='reason', help='Reason for the warn.')
        parser.add_argument('-c', '--count', metavar='count', type=int, help='Number of warnings to add.')
        try:
            args = parser.parse_args(args)
        except Exception as e:
            return await ctx.send(e)
        people = []
        count = args.count or 1
        if count > 50:
            return await ctx.send(':x: Maximum warn weight for a single warning is 50.')
        if count <= 0:
            return await ctx.send(':x: Count must be 1 or above.')
        for i in args.users:
            try:
                m = await commands.MemberConverter().convert(ctx, i)
            except commands.errors.BadArgument as e:
                return await ctx.send(f':x: | {e}')
            people.append(m)
        for i in people:
            self._add_warning(ctx, i, args.reason, count)
        await ctx.send('Okay, warned.')
        await self._send_warn_embed(ctx, people, args.reason, count=count)
    
    @commands.command(aliases=['uw', 'unwarn'])
    async def pardon(self, ctx, *args):
        """Removes a warning"""
        selfperms = ctx.author.permissions_in(ctx.channel)
        hasperm = (
            selfperms.kick_members or
            selfperms.ban_members or
            selfperms.manage_roles
        )
        if not hasperm:
            return await ctx.send(':no_entry_sign: Invalid permissions.')
        parser = argparse.DiscordFriendlyArgparse(prog=ctx.invoked_with, add_help=True)
        parser.add_argument('-u', '--users', nargs='+', required=True, metavar='@user', help='List of users to warn.')
        parser.add_argument('-r', '--reason', required=True, metavar='reason', help='Reason for the pardon.')
        parser.add_argument('-c', '--count', metavar='count', type=int, help='Number of warnings to remove.')
        try:
            args = parser.parse_args(args)
        except Exception as e:
            return await ctx.send(e)
        people = []
        count = args.count or 1
        if count <= 0:
            return await ctx.send(':x: Count must be 1 or above.')
        for i in args.users:
            try:
                m = await commands.MemberConverter().convert(ctx, i)
            except commands.errors.BadArgument as e:
                return await ctx.send(f':x: | {e}')
            people.append(m)
        for i in people:
            c = self._remove_warnings(ctx, i, count)
            if not c:
                return await ctx.send(':x: You cannot pardon a user with no warnings.')
        await self._send_pardon_embed(ctx, people, args.reason, count)
        await ctx.send('Okay, pardoned.')

    @commands.command(aliases=['ezw'])
    async def ezwarn(self, ctx, user:discord.Member, reason):
        """Warn but divided by 2"""
        selfperms = ctx.author.permissions_in(ctx.channel)
        hasperm = (
            selfperms.kick_members or
            selfperms.ban_members or
            selfperms.manage_roles
        )
        if not hasperm:
            return await ctx.send(':no_entry_sign: Invalid permissions.')
        self._add_warning(ctx, user, reason)
        await self._send_warn_embed(ctx, [user], reason, 1)
        await ctx.send('Okay, warned.')

    @commands.command(aliases=['ezp', 'ezuw'])
    async def ezpardon(self, ctx, user:discord.Member, count:int, reason):
        """Pardon but divided by 2"""
        selfperms = ctx.author.permissions_in(ctx.channel)
        hasperm = (
            selfperms.kick_members or
            selfperms.ban_members or
            selfperms.manage_roles
        )
        if not hasperm:
            return await ctx.send(':no_entry_sign: Invalid permissions.')
        if count <= 0:
            return await ctx.send(':x: Count must be 1 or above.')
        self._remove_warnings(ctx, user, reason)
        await self._send_warn_embed(ctx, [user], reason, count)
        await ctx.send('Okay, pardoned.')

    async def get_user(self, uid: int):
        user = None  # database fetch
        if user is not None:
            # noinspection PyProtectedMember
            return discord.User(state=self.bot._connection, data=user) # I'm sorry Danny

        user = self.bot.get_user(uid)
        if user is not None:
            return user

        try:
            user = await self.bot.get_user_info(uid)
        except discord.NotFound:
            user = None
        if user is not None:  # intentionally leaving this at the end so we can add more methods after this one
            return user

    @commands.command(aliases=['warns'])
    async def check_warnings(self, ctx, member:discord.Member=None):
        """Check your or another user's warnings"""
        selfperms = ctx.author.permissions_in(ctx.channel)
        hasperm = (
            selfperms.kick_members or
            selfperms.ban_members or
            selfperms.manage_roles
        )
        user = member if hasperm and member else ctx.author
        warns = self.get_warnings(user, ctx.guild)
        embed = discord.Embed()
        if warns is None or len(warns) == 0:
            embed.description = 'You have no warnings.'
            embed.colour = 0x2C2F33
            return await ctx.send(embed=embed)
        colour = colours[self._calculate_stage(self._calculate_total(warns))]
        embed.colour = colour
        if len(warns) > 15:
            warnstr = ''
            for i in warns:
                mod = await self.get_user(int(i['mod']))
                warnstr += f'{i["reason"]} (by {mod}, weighted {i["weight"]})\n'
            warnstring += f'Total: {self._calculate_total(warns)} ({len(warns)})'
            hid = await self.haste_upload(warnstring)
            embed.description = f'[View on hastebin](https://hastebin.com/{hid})'
        else:
            for n, i in enumerate(warns):
                mod = await self.get_user(int(i['mod']))
                embed.add_field(name=f'#{n+1} (by {mod}, weighted {i["weight"]})', value=i['reason'], inline=False)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Warnings(bot))
