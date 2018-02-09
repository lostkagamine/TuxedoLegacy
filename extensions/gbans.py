# Global ban cog for Tuxedo
# flake8: noqa E501
import discord
from discord.ext import commands
import rethinkdb as r
from utils import permissions
import aiohttp
from utils.argparse import DiscordFriendlyArgparse, DiscordArgparseError, DiscordArgparseMessage

class GbanException(Exception):
    pass


class Gbans:
    def __init__(self, bot):
        self.conn = bot.conn
        self.bot = bot
        self.token = bot.config.get('GBANS_TOKEN')

        @bot.listen('on_member_join')
        async def on_member_join(u):
            g = u.guild
            exists = (lambda: list(r.table('settings').filter(
                lambda a: a['guild'] == str(g.id)).run(self.conn)) != [])()
            if not exists:
                return
            # we know the guild has an entry in the settings
            settings = list(r.table('settings').filter(
                lambda a: a['guild'] == str(g.id)).run(self.conn))[0]
            if "global_bans" not in settings.keys():
                return
            if not settings['global_bans']:
                return
            try:
                if await self.is_gbanned(u.id):
                    nomsg = False
                    try:
                        details = self.gban_details(u.id)
                        if details['moderator'] != None:
                            mod = await self.get_user(int(details['moderator']))
                            modstr = f'**{mod.name}**#{mod.discriminator} ({mod.id})'
                        else:
                            modstr = '**Unknown moderator**'
                        msg = await u.send(f'''
**You were banned automatically from {g}.**
The reason for this was that you are globally banned.
The mod that banned you was {modstr}. Contact them for further info.
You were banned for `{details['reason']}` with proof `{details['proof']}`.
                        ''')
                    except discord.Forbidden:
                        nomsg = True
                    await u.ban(reason='[Automatic - user globally banned]')
            except discord.Forbidden:
                if nomsg:
                    return
                else:
                    await msg.delete()

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

    async def ban(self, uid: int, mod: int, reason: str='<none specified>', proof: str='<none specified>'):
        'Easy interface with the global banner'
        if str(uid) in self.bot.config.get('OWNERS') or str(uid) in self.bot.config.get('GLOBAL_MODS'):
            raise GbanException('You cannot ban a bot owner/global moderator.')
        if uid == self.bot.user.id:
            raise GbanException(
                'You cannot ban the bot itself. Duh, did you think I\'d let you?')
        if await self.is_gbanned(uid):
            raise GbanException(f'ID {uid} is already globally banned.')
        r.table('gbans').insert({
            'user': str(uid),
            'moderator': str(mod),
            'proof': str(proof),
            'reason': str(reason)
        }, conflict='update').run(self.conn)
        hss = aiohttp.ClientSession()
        async with hss.put(f'https://api-pandentia.qcx.io/discord/global_bans/{uid}', headers={'Authorization': self.token},
                           json={'moderator': mod, 'reason': reason, 'proof': proof}) as resp:
            if resp.status == 401:
                raise GbanException(
                    f'Uh-oh, the API returned Forbidden. Check your token.')
            elif resp.status == 409:
                raise GbanException(
                    f'This user is already remotely banned. They have been banned locally.')
        await hss.close()
        print(
            f'[Global bans] {mod} has just banned {uid} globally for {reason} with proof {proof}')

    async def unban(self, uid: int):
        'Easy interface with the global banner'
        if not await self.is_gbanned(uid):
            raise GbanException(f'ID {uid} wasn\'t globally banned.')
        r.table('gbans').filter({'user': str(uid)}).delete().run(self.conn)
        hss = aiohttp.ClientSession()
        async with hss.delete(f'https://api-pandentia.qcx.io/discord/global_bans/{uid}', headers={'Authorization': self.token}) as resp:
            if resp.status == 401:
                raise GbanException(
                    f'Uh-oh, the API returned Forbidden. Check your token.')
        await hss.close()
        print(f'[Global bans] {uid} just got globally unbanned')

    async def is_gbanned(self, user: int):
        try:
            meme = r.table('gbans').filter(
                {'user': str(user)}).run(self.conn).next()
            return True  # is gbanned
        except Exception:  # local then remote
            hss = aiohttp.ClientSession()
            async with hss.get(f'https://api-pandentia.qcx.io/discord/global_bans/{user}') as resp:
                if resp.status == 200:
                    return True
                else:
                    return False
            await hss.close()

    async def gban_details(self, user: int):
        try:
            meme = r.table('gbans').filter(
                {'user': str(user)}).run(self.conn).next()
            return meme
        except Exception:  # *not* locally banned
            hss = aiohttp.ClientSession()
            async with hss.get(f'https://api-pandentia.qcx.io/discord/global_bans/{user}') as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return None
            await hss.close()

    @commands.group(name='gban', aliases=['gbans', 'globalbans', 'global_bans'], invoke_without_command=True)
    async def gban(self, ctx, param):
        """Globally bans a user."""
        raise commands.errors.MissingRequiredArgument()

    @gban.command(aliases=['new', 'ban'])
    @permissions.owner_or_gmod()
    async def add(self, ctx, *args):
        parser = DiscordFriendlyArgparse(prog=ctx.command.name, add_help=True)
        parser.add_argument('-u', '--users', nargs='+', type=int,
                            metavar='ID', required=True, help='List of users to ban.')
        parser.add_argument('-r', '--reason', help='A reason for the ban.')
        parser.add_argument('-p', '--proof', help='A proof for the ban.')
        try:
            args = parser.parse_args(args)
        except DiscordArgparseError as e:
            return await ctx.send(str(e))
        if args.reason == None and args.proof == None:
            return await ctx.send('Specify either a reason or proof.')
        for uid in args.users:
            try:
                await self.ban(uid, ctx.author.id, args.reason, args.proof)
            except GbanException as e:
                return await ctx.send(f':x: {e}')
        actual_u = [await self.get_user(i) for i in args.users]
        for k, v in enumerate(actual_u):
            if v == None:
                actual_u[k] = 'Unknown'
        for g in ctx.bot.guilds:
            try:
                settings = list(r.table('settings').filter(
                    lambda a: a['guild'] == str(g.id)).run(self.conn))[0]
            except Exception:
                continue
            if "gban_alerts" not in settings.keys():
                continue
            chan = g.get_channel(int(settings['gban_alerts']))
            if chan != None:
                try:
                    await chan.send(f':hammer: {", ".join([str(i) for i in actual_u])} {"has" if len(actual_u) == 1 else "have"} been globally banned.\nReason given: `{args.reason}`\nProof given: `{args.proof}`')
                except discord.Forbidden:
                    pass
        await ctx.send(f'User(s) banned for reason `{args.reason}` with proof `{args.proof}`.')

    @gban.command(aliases=['rm', 'delete', 'unban'])
    @permissions.owner_or_gmod()
    async def remove(self, ctx, *args):
        parser = DiscordFriendlyArgparse(prog=ctx.command.name, add_help=True)
        parser.add_argument('-u', '--users', nargs='+', type=int,
                            metavar='ID', required=True, help='List of users to unban.')
        parser.add_argument('-r', '--reason', help='Reason for unbanning.')
        parser.add_argument('-p', '--proof', help='Proof for unbanning.')
        try:
            args = parser.parse_args(args)
        except DiscordArgparseError as e:
            return await ctx.send(str(e))
        for uid in args.users:
            try:
                await self.unban(uid)
            except GbanException as e:
                return await ctx.send(f':x: {e}')
        actual_u = [await self.get_user(i) for i in args.users]
        for k, v in enumerate(actual_u):
            if v == None:
                actual_u[k] = 'Unknown'
        for g in ctx.bot.guilds:
            try:
                settings = list(r.table('settings').filter(
                    lambda a: a['guild'] == str(g.id)).run(self.conn))[0]
            except Exception:
                continue
            if "gban_alerts" not in settings.keys():
                continue
            chan = g.get_channel(int(settings['gban_alerts']))
            if chan != None:
                try:
                    await chan.send(f'<:tuxAlert:390564666977419264> {", ".join([str(i) for i in actual_u])} {"has" if len(actual_u) == 1 else "have"} been globally unbanned.\nReason given: `{args.reason}`\nProof given: `{args.proof}`')
                except discord.Forbidden:
                    pass
        await ctx.send('User(s) unbanned successfully.')

    @gban.command()
    async def check(self, ctx, *args):
        parser = DiscordFriendlyArgparse(prog=ctx.command.name, add_help=True)
        parser.add_argument('-u', '--users', nargs='+', type=int,
                            metavar='ID', required=True, help='List of users to check for.')
        try:
            args = parser.parse_args(args)
        except DiscordArgparseError as e:
            return await ctx.send(str(e))
        embed = discord.Embed(title='Global ban info')
        for uid in args.users:
            user = await self.get_user(uid)
            if user == None:
                ustring = f'Unknown ({uid})'
            else:
                ustring = f'**{user.name}**#{user.discriminator}'
            isban = await self.is_gbanned(uid)
            detail = await self.gban_details(uid)
            if isban:
                if detail['moderator'] != None:
                    mod = await self.get_user(detail['moderator'])
                else:
                    mod = 'Unknown'
            print(detail)
            stri = f'''
Globally banned? {"<:check:314349398811475968>" if isban else "<:xmark:314349398824058880>"}{f"""
Banned by: {mod}
Reason: {detail['reason']}
Proof: {detail['proof']}
""" if detail != None else ""}'''
            embed.add_field(name=ustring, value=stri)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Gbans(bot))
