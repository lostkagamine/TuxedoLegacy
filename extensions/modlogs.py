import rethinkdb as r
import discord
from discord.ext import commands
import asyncio
from utils import permissions
import shlex

settings = {'modlog_channel': 'channel', 'enable_invite_protection': 'bool', 'staff_channel': 'channel', 'tracked_roles': 'rolelist'}

templates = {'ban': '**User Ban** | Case {id}\n**Target:** {user}\n**Moderator:** {mod}\n**Reason:** {rsn}',
             'kick': '**User Kick** | Case {id}\n**Target:** {user}\n**Moderator:** {mod}\n**Reason:** {rsn}',
             'unban': '**User Unban** | Case {id}\n**Target:** {user}\n**Moderator:** {mod}\n**Reason:** {rsn}',
             'role_add': '**Role Add** | Case {id}\n**Role:** {role}\n**Target:** {user}\n**Moderator:** {mod}\n**Reason:** {rsn}',
             'role_remove': '**Role Remove** | Case {id}\n**Role:** {role}\n**Target:** {user}\n**Moderator:** {mod}\n**Reason:** {rsn}'}

categories = {'ban': discord.AuditLogAction.ban,
              'kick': discord.AuditLogAction.kick,
              'unban': discord.AuditLogAction.unban,
              'role_add': discord.AuditLogAction.member_role_update,
              'role_remove': discord.AuditLogAction.member_role_update}


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

    def process_template(self, template, user, mod, reason, case='Unknown', role='N/A'):
        return templates[template].replace('{user}', user).replace('{mod}', mod).replace('{rsn}', reason).replace('{id}', str(case)).replace('{role}', role)

    async def do_modlog(self, _type, g, u):
        ch = self.modlog_ch(g)
        if ch == None: return
        try:
            await asyncio.sleep(0.10)
            async for audit in g.audit_logs(limit=1, action=categories[_type]):
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
        if ch == None: return
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
            await asyncio.sleep(0.10)
            async for audit in g.audit_logs(limit=1):
                if audit.target.id == m.id and audit.action == discord.AuditLogAction.kick:
                    await self.do_modlog_raw('kick', g, m,
                                             audit.reason if audit.reason else 'Unknown', audit.user)

        @self.bot.listen('on_member_unban')
        async def on_member_unban(g, u):
            await self.do_modlog('unban', g, u)

        @self.bot.listen('on_member_update')
        async def on_member_update(before, after):
            if before.roles == after.roles:
                return # no role changes, we can drop it
            exists = (lambda: list(r.table('settings').filter(
                lambda a: a['guild'] == str(g.id)).run(self.conn)) != [])()
            if not exists:
                return
            # we know the guild has an entry in the settings
            settings = list(r.table('settings').filter(
                lambda a: a['guild'] == str(g.id)).run(self.conn))[0]
            if "tracked_roles" not in settings.keys():
                return
            for i in [str(r.id) for i in after.roles]:
                if i in settings['tracked_roles']:


    def check_type(self, ctx, thing, value):
        if thing == "channel":
            return hasattr(ctx.message, 'channel_mentions')
        elif thing == 'bool':
            return value.lower() in ['true', 'false']
        elif thing == ('rolelist'):
            try:
                shlex.split(value)
                return True
            except Exception:
                return False

    def do_type(self, ctx, _type, value):
        print(value)
        if _type == "channel":
            return str(ctx.message.channel_mentions[0].id)
        elif _type == 'bool':
            if value.lower() in ['true', 'false']:
                return value.lower() == 'true'
        elif _type == 'rolelist':
            roles = self.do_list(ctx, value)
            if roles == False:
                return 'ERR|One or more roles not found. Make sure to use \' instead of ".'
            return [str(i.id) for i in roles]

    def do_list(self, ctx, stuff):
        aaaa = shlex.split(stuff)
        roles = []
        for i in aaaa:
            role = discord.utils.find(lambda a: a.name == i, ctx.guild.roles)
            if role == None:
                return False
            roles.append(role)
        return roles
            

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
        if not self.check_type(ctx, settings[thing_to_set], ' '.join(args[1:len(args)])):
            return await ctx.send(':x: This property is of type `{}`.'.format(settings[thing_to_set]))
        data = {'guild': str(ctx.guild.id)}
        setting = self.do_type(ctx, settings[thing_to_set], ' '.join(args[1:len(args)]).replace('"', "'"))
        if isinstance(setting, str):
            if setting.startswith('ERR'):
                stuff = setting.split('|')
                return await ctx.send(f':x: An error occurred. `{stuff[1]}`')
        data[thing_to_set] = setting
        exists = (lambda: list(r.table('settings').filter(
            lambda a: a['guild'] == str(ctx.guild.id)).run(self.conn)) != [])()
        if exists:
            r.table('settings').filter(lambda a: a['guild'] == str(
                ctx.guild.id)).update(data).run(self.conn)
        else:
            r.table('settings').insert(data, conflict='replace').run(self.conn)
        await ctx.send(':ok_hand:')

    @commands.command(aliases=['cfg'])
    async def view_config(self, ctx):
        exists = (lambda: list(r.table('settings').filter(
            lambda a: a['guild'] == str(ctx.guild.id)).run(self.conn)) != [])()
        if not exists:
            return await ctx.send(':x: This guild has no configuration.')
        meme = r.table('settings').filter(lambda a: a['guild'] == str(
            ctx.guild.id)).run(self.conn)
        meme = meme.next()
        await ctx.send(f'```{meme}```')

    @commands.command(aliases=['delcfg'])
    async def delete_config(self, ctx):
        exists = (lambda: list(r.table('settings').filter(
            lambda a: a['guild'] == str(ctx.guild.id)).run(self.conn)) != [])()
        if not exists:
            return await ctx.send(':x: This guild has no configuration.')
        meme = r.table('settings').filter(lambda a: a['guild'] == str(
            ctx.guild.id)).delete().run(self.conn)
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
        if caseid < 1 or caseid > data['count']: return await ctx.send(':x: List index out of range. (Invalid Case ID)')
        entry = data['entries'][caseid-1]
        entry['mod'] = f'{str(ctx.author)} ({ctx.author.id})'
        entry['reason'] = reason
        msgid = int(entry['msgid'])
        channel = self.modlog_ch(ctx.guild)
        if channel == None: return
        chid = channel.id
        msgs = []
        async for i in channel.history(limit=500):
            msgs.append(i)
        msg = discord.utils.find(lambda a: a.id == int(entry['msgid']), msgs)
        if msg == None: return await ctx.send(':x: No modlog entry found.')
        await msg.edit(content=self.process_template(
            entry['type'],
            entry['target'],
            entry['mod'],
            entry['reason'],
            caseid
        ))
        await ctx.send(':ok_hand:')

def setup(bot):
    bot.add_cog(ModLogs(bot))
