import rethinkdb as r
import discord
from discord.ext import commands
import asyncio
from utils import permissions

settings = {'modlog_channel': 'channel'}

templates = {'ban': '**User Ban** | Case {id}\n\n**Target:** {user}\n**Moderator:** {mod}\n**Reason:** {rsn}',
             'kick': '**User Kick** | Case {id}\n\n**Target:** {user}\n**Moderator:** {mod}\n**Reason:** {rsn}',
             'unban': '**User Unban** | Case {id}\n\n**Target:** {user}\n**Moderator:** {mod}\n**Reason:** {rsn}'}


class ModLogs:
    async def log_entry(self, _type, guild, target, mod, reason, msgid):
        data = {
            'guild': str(guild.id),
            'target': target,
            'mod': mod,
            'reason': reason,
            'msgid': msgid,
            'type': _type
        }
        objdata = {
            'entries': [],
            'guild': str(guild.id),
            'count': 0
        }
        exists = (lambda: list(r.table('modlog').filter(
            lambda a: a['guild'] == str(guild.id)).run(self.conn)) != [])()
        if exists:
            # do stuff
            log = r.table('modlog').filter(
                lambda a: a['guild'] == str(guild.id)).run(self.conn)
            stuff = log.next()
            entries = stuff['entries']
            entries.append(data)
            stuff['count'] = len(entries)
            r.table('modlog').filter(lambda a: a['guild'] == str(
                guild.id)).update(stuff).run(self.conn)
            count = stuff['count']
        else:
            # do other stuff I :thonk:
            aaa = objdata
            aaa['entries'].append(data)
            aaa['count'] = 1
            r.table('modlog').insert(aaa, conflict='replace').run(self.conn)
            count = aaa['count']

        return count

    def modlog_ch(self, g):
        exists = (lambda: list(r.table('settings').filter(
            lambda a: a['guild'] == str(g.id)).run(self.conn)) != [])()
        if not exists:
            return
        # we know the guild has an entry in the settings
        settings = list(r.table('settings').filter(
            lambda a: a['guild'] == str(g.id)).run(self.conn))[0]
        if "modlog_channel" not in settings.keys():
            return
        return discord.utils.find(lambda a: str(a.id) == settings.get('modlog_channel'), g.text_channels)

    def process_template(self, template, user, mod, reason, case='Unknown'):
        return templates[template].replace('{user}', user).replace('{mod}', mod).replace('{rsn}', reason).replace('{id}', str(case))

    async def do_modlog(self, _type, g, u):
        ch = self.modlog_ch(g)
        try:
            async for audit in g.audit_logs(limit=1):
                msg = await ch.send(self.process_template(_type, f'{str(u)} ({u.id})',
                                                          f'{str(audit.user)} ({audit.user.id})', audit.reason if audit.reason else 'Unknown'))
                cid = await self.log_entry(_type, g, f'{str(u)} ({u.id})', f'{str(audit.user)} ({audit.user.id})', audit.reason if audit.reason else 'Unknown', str(msg.id))
                await msg.edit(content=self.process_template(_type, f'{str(u)} ({u.id})',
                                                             f'{str(audit.user)} ({audit.user.id})', audit.reason if audit.reason else 'Unknown',
                                                             str(cid)))
        except discord.Forbidden:
            await ch.send(self.process_template(_type, str(u), 'Unknown moderator', 'Unknown. Please grant the bot `View Audit Logs`.'))

    async def do_modlog_raw(self, _type, g, u, reason, mod):
        ch = self.modlog_ch(g)
        msg = await ch.send(self.process_template(_type, f'{str(u)} ({u.id})',
                                                  f'{str(mod)} ({mod.id})', reason if reason else 'Unknown'))
        cid = await self.log_entry(_type, g, f'{str(u)} ({u.id})', f'{str(mod)} ({mod.id})', reason if reason else 'Unknown', str(msg.id))
        await msg.edit(content=self.process_template(_type, f'{str(u)} ({u.id})',
                                                     f'{str(mod)} ({mod.id})', reason if reason else 'Unknown',
                                                     str(cid)))

    def check_perm(self, ctx):
        return (ctx.author.permissions_in(ctx.channel).manage_guild) or (permissions.owner_id_check(ctx.author.id))

    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.conn

        @self.bot.listen("on_member_ban")
        async def on_member_ban(g, u):
            await self.do_modlog('ban', g, u)

        @self.bot.listen('on_member_remove')
        async def on_member_remove(m):
            g = m.guild
            async for audit in g.audit_logs(limit=1):
                if audit.target.id == m.id and audit.action == discord.AuditLogAction.kick:
                    await self.do_modlog_raw('kick', g, m,
                                             audit.reason if audit.reason else 'Unknown', audit.user)

        @self.bot.listen('on_member_unban')
        async def on_member_unban(g, u):
            await self.do_modlog('unban', g, u)

    def check_type(self, ctx, thing):
        if thing == "channel":
            return hasattr(ctx.message, 'channel_mentions')

    def do_type(self, ctx, _type):
        if _type == "channel":
            return str(ctx.message.channel_mentions[0].id)

    @commands.command(name='set', aliases=['settings', 'setup', 'setting'])
    async def _set(self, ctx, *args):
        settings_str = ', '.join(settings)
        if len(args) <= 0:
            return await ctx.send(':x: Please specify a value to set.')
        if not self.check_perm(ctx):
            return await ctx.send(':no_entry_sign: Invalid permissions.')
        thing_to_set = args[0]
        if thing_to_set not in settings.keys():
            return await ctx.send(f':x: Invalid value. Possible values are: `{settings_str}`')
        if not self.check_type(ctx, settings[thing_to_set]):
            return await ctx.send(':x: This property is of type `{}`.'.format(settings[thing_to_set]))
        data = {'guild': str(ctx.guild.id)}
        data[thing_to_set] = self.do_type(ctx, settings[thing_to_set])
        exists = (lambda: list(r.table('settings').filter(
            lambda a: a['guild'] == str(ctx.guild.id)).run(self.conn)) != [])()
        if exists:
            r.table('settings').filter(lambda a: a['guild'] == str(
                ctx.guild.id)).update(data).run(self.conn)
        else:
            r.table('settings').insert(data, conflict='replace').run(self.conn)
        await ctx.send(':ok_hand:')

    @commands.command(hidden=True)
    @permissions.owner()
    async def wipe_all_settings(self, ctx):
        await ctx.send("Are you **sure**? This will wipe everything! Type `Yes, do it!` to confirm. (10 seconds)")
        try:
            msg = await ctx.bot.wait_for('message',
                                         check=lambda a: a.author == ctx.author and a.content == "Yes, do it!" and a.channel == ctx.channel,
                                         timeout=10.0)
        except asyncio.TimeoutError:
            return await ctx.send('Cancelled.')

        r.table('settings').delete().run(self.conn)
        await ctx.send(':ok_hand:')

    @commands.command(hidden=True)
    @permissions.owner()
    async def wipe_all_cases(self, ctx):
        await ctx.send("Are you **sure**? This will wipe everything! Type `Yes, do it!` to confirm. (10 seconds)")
        try:
            msg = await ctx.bot.wait_for('message',
                                         check=lambda a: a.author == ctx.author and a.content == "Yes, do it!" and a.channel == ctx.channel,
                                         timeout=10.0)
        except asyncio.TimeoutError:
            return await ctx.send('Cancelled.')

        r.table('modlog').delete().run(self.conn)
        await ctx.send(':ok_hand:')

    @commands.command()
    async def reason(self, ctx, caseid: int, *, reason: str):
        exists = (lambda: list(r.table('modlog').filter(
            lambda a: a['guild'] == str(ctx.guild.id)).run(self.conn)) != [])()
        if not exists:
            return await ctx.send(':x: This guild has no modlog entries.')
        if not self.check_perm(ctx):
            return await ctx.send(':no_entry_sign: Invalid permissions.')
        data = r.table('modlog').filter(
            lambda a: a['guild'] == str(ctx.guild.id)).run(self.conn)
        data = data.next()
        # print(data)
        if len(data['entries']) < caseid-1 or len(data['entries']) > caseid: return await ctx.send(':x: List index out of range.')
        entry = data['entries'][caseid-1]
        entry['mod'] = f'{str(ctx.author)} ({ctx.author.id})'
        entry['reason'] = reason
        msgid = int(entry['msgid'])
        channel = self.modlog_ch(ctx.guild)
        chid = channel.id
        msgs = []
        async for i in channel.history(limit=500):
            msgs.append(i)
        msg = discord.utils.find(lambda a: a.id == int(entry['msgid']), msgs)
        if msg is None: return await ctx.send(':x: No modlog entry found.')
        await msg.edit(content=self.process_template(
            entry['type'],
            entry['target'],
            entry['mod'],
            entry['reason'],
            len(data['entries'])
        ))
        r.table('modlog').filter(lambda a: a['guild'] == str(ctx.guild.id)).update(data).run(self.conn)
        await ctx.send(':ok_hand:')

def setup(bot):
    bot.add_cog(ModLogs(bot))
