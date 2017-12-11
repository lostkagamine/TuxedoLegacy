# Global ban cog for Tuxedo

import discord
from discord.ext import commands
import rethinkdb as r 
from utils import permissions

class GbanException(Exception):
    pass

class Gbans:
    def __init__(self, bot):
        self.conn = bot.conn
        self.bot = bot
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
                if self.is_gbanned(u.id):
                    nomsg = False
                    try:
                        details = self.gban_details(u.id)
                        msg = await u.send(f'''
**You were banned automatically from {g}.**
The reason for this was that you are globally banned.
The mod that banned you was {details['modstr']}. Contact them for further info.
You were banned for {details['reason']} with proof {details['proof']}.
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
    
    async def ban(self, uid:int, mod:int, reason:str='<none specified>', proof:str='<none specified>'):
        'Easy interface with the global banner'
        user = await self.get_user(uid)
        moderator = await self.get_user(mod)
        if self.is_gbanned(uid):
            raise GbanException('This user is already globally banned.')
        if not (user != None and moderator != None):
            raise GbanException('An invalid user or moderator was passed.')
        r.table('gbans').insert({
            'user': str(uid),
            'ustr': f'{user.name}#{user.discriminator} ({uid})',
            'mod': str(mod),
            'modstr': f'{moderator.name}#{moderator.discriminator} ({mod})',
            'proof': proof,
            'reason': reason
        }, conflict='update').run(self.conn)
        print(f'[Global bans] {moderator} has just banned {user} globally for {reason} with proof {proof}')

    async def unban(self, uid:int):
        'Easy interface with the global banner'
        user = await self.get_user(uid)
        if not self.is_gbanned(uid):
            raise GbanException('This user wasn\'t globally banned.')
        if not (user != None):
            raise GbanException('An invalid user was passed.')
        r.table('gbans').filter({'user': str(uid)}).delete().run(self.conn)
        print(f'[Global bans] {user} just got globally unbanned')
    
    def is_gbanned(self, user:int):
        try:
            meme = r.table('gbans').filter({'user': str(user)}).run(self.conn).next()
            return True # is gbanned
        except Exception:
            return False

    def gban_details(self, user:int):
        try:
            meme = r.table('gbans').filter({'user': str(user)}).run(self.conn).next()
            return meme
        except Exception:
            return None

    @commands.group(name='gban', aliases=['gbans', 'globalbans', 'global_bans'], invoke_without_command=True)
    async def gban(self, ctx, param):
        raise commands.errors.MissingRequiredArgument()

    @gban.command(aliases=['new', 'ban'])
    @permissions.owner_or_gmod()
    async def add(self, ctx, user, reason:str='<none specified>', proof:str='<none specified>'):
        if type(user) == str: 
            try:
                user = int(user)
                puser = await self.get_user(user)
                uid = user
            except ValueError:
                return
        elif type(user) == discord.Member: puser = user
        else: return
        if puser == None: return await ctx.send(':x: An invalid user was passed. Mention or use an ID that is present to the bot.')
        uid = puser.id
        try:
            await self.ban(uid, ctx.author.id, reason, proof)
            await ctx.send(f'**{puser.name}**#{puser.discriminator} ({puser.id}) has been globally banned. RIP in peace.')
        except GbanException as e:
            await ctx.send(f':x: {e}')

    @gban.command(aliases=['rm', 'delete', 'unban'])
    @permissions.owner_or_gmod()
    async def remove(self, ctx, user):
        if type(user) == str: 
            try:
                user = int(user)
                puser = await self.get_user(user)
                uid = user
            except ValueError:
                return
        elif type(user) == discord.Member: puser = user
        else: return
        if puser == None: return await ctx.send(':x: An invalid user was passed. Mention or use an ID that is present to the bot.')
        uid = puser.id
        try:
            await self.unban(uid)
            await ctx.send(f'**{puser.name}**#{puser.discriminator} ({puser.id}) has been globally unbanned.')
        except GbanException as e:
            await ctx.send(f':x: {e}')

    @gban.command()
    async def check(self, ctx, user):
        if type(user) == str: 
            try:
                user = int(user)
                puser = await self.get_user(user)
                uid = user
            except ValueError:
                return
        elif type(user) == discord.Member: puser = user
        else: return
        if puser == None: return await ctx.send(':x: An invalid user was passed. Mention or use an ID that is present to the bot.')
        uid = puser.id
        details = self.gban_details(uid)
        mod = str(puser.id) in ctx.bot.config.get('OWNERS')
        embed = discord.Embed(title=f'Global ban statistics for {puser}{" (Global Moderator)" if mod else ""}')
        if details != None:
            embed.colour = 0xFF0000
            embed.add_field(name='__This user is globally banned.__', value=f'Banned by: {details["modstr"]}\nReason: {details["reason"]}\nProof: {details["proof"]}')
        else:
            embed.colour = 0x00FF00
            embed.description = 'This user isn\'t globally banned.'
        if mod:
            embed.colour = 0x00C8C8
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Gbans(bot))
