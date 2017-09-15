import rethinkdb as r 
import discord
from discord.ext import commands

settings = {'modlog_channel': 'channel'}

templates = {'ban': '**User Ban**\n\n**Target:** {user}\n**Moderator:** {mod}\n**Reason:** {rsn}',
            'kick': '**User Kick**\n\n**Target:** {user}\n**Moderator:** {mod}\n**Reason:** {rsn}',
            'unban': '**User Unban**\n\n**Target:** {user}\n**Moderator:** {mod}\n**Reason:** {rsn}'}

class ModLogs:
    def modlog_ch(self, g):
        exists = (lambda: list(r.table('settings').filter(lambda a: a['guild'] == str(g.id)).run(self.conn)) != [])()
        if not exists: return
        # we know the guild has an entry in the settings
        settings = list(r.table('settings').filter(lambda a: a['guild'] == str(g.id)).run(self.conn))[0]
        if "modlog_channel" not in settings.keys(): return
        return discord.utils.find(lambda a: str(a.id) == settings.get('modlog_channel'), g.text_channels)
    
    def process_template(self, template, user, mod, reason):
        return templates[template].replace('{user}', user).replace('{mod}', mod).replace('{rsn}', reason)

    async def do_modlog(self, _type, g, u):
        ch = self.modlog_ch(g)
        try:
            async for audit in g.audit_logs(limit=1):
                await ch.send(self.process_template(_type, f'{str(u)} ({u.id})', f'{str(audit.user)} ({audit.user.id})', audit.reason if audit.reason else 'Unknown'))
        except discord.Forbidden:
            await ch.send(self.process_template(_type, str(u), 'Unknown moderator', 'Unknown. Please grant the bot `View Audit Logs`.'))

    async def do_modlog_raw(self, _type, g, u, reason, mod):
        ch = self.modlog_ch(g)
        await ch.send(self.process_template(_type, u, mod, reason))

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
                    await self.do_modlog_raw('kick', g, f'{str(m)} ({m.id})', audit.reason if audit.reason else 'Unknown', f'{str(audit.user)} ({audit.user.id})')
        
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
        if not ctx.author.permissions_in(ctx.channel).manage_guild:
            return await ctx.send(':no_entry_sign: Not enough permissions.')
        thing_to_set = args[0]
        if thing_to_set not in settings.keys():
            return await ctx.send(f':x: Invalid value. Possible values are: `{settings_str}`')
        if not self.check_type(ctx, settings[thing_to_set]): return await ctx.send(':x: This property is of type `{}`.'.format(settings[thing_to_set]))
        data = {'guild': str(ctx.guild.id)}
        data[thing_to_set] = self.do_type(ctx, settings[thing_to_set])
        exists = (lambda: list(r.table('settings').filter(lambda a: a['guild'] == str(ctx.guild.id)).run(self.conn)) != [])()
        if exists:
            r.table('settings').filter(lambda a: a['guild'] == str(ctx.guild.id)).update(data).run(self.conn)
        else:
            r.table('settings').insert(data, conflict='replace').run(self.conn)
        await ctx.send(':ok_hand:')

def setup(bot):
    bot.add_cog(ModLogs(bot))
