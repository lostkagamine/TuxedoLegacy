import traceback
import json
import discord
from discord.ext import commands
from discord.ext.commands import errors as commands_errors
from discord import utils as dutils
import random
import asyncio
import raven
import rethinkdb as r
import re
import sys
import datetime
from discord.ext.commands.view import StringView
from utils import permissions
nopls = [110373943822540800, 264445053596991498]

asd = 236726289665490944  # Automatic Sink Detection (tm)


class Bot(commands.Bot):
    def __init__(self, **options):
        super().__init__(self.getPrefix, **options)
        print('Performing pre-run tasks...')
        self.maintenance = False
        with open("config.json") as f:
            self.config = json.load(f)
            self.prefix = self.config.get('BOT_PREFIX')
            self.version = self.config.get('VERSION')
            self.do_sentry = self.config.get('SENTRY_ENABLED')
        self.remove_command("help")
        if self.do_sentry:
            self.init_raven()
        self.rdb = self.config['RETHINKDB']['DB']
        self.rtables = ['gbans', 'settings', 'modlog',
                        'tempbans', 'starboard', 'warnings']
        self.init_rethinkdb()
        print('Pre-run tasks complete.')

    async def get_context(self, message, *, cls=discord.ext.commands.Context):  # perryyyyyyyy
        view = StringView(message.content)
        ctx = cls(prefix=None, view=view, bot=self, message=message)

        if self._skip_check(message.author.id, self.user.id):
            return ctx

        prefix = await self.get_prefix(message)
        invoked_prefix = prefix

        if isinstance(prefix, str):
            if not view.skip_string(prefix):
                return ctx
        elif isinstance(prefix, list) \
                and any([isinstance(p, list) for p in prefix]):
            # Regex time
            for p in prefix:
                if isinstance(p, list):
                    if p[1]:
                        # regex prefix parsing
                        reg = re.match(p[0], message.content)
                        if reg:
                            # Matches, this is the prefix
                            invoked_prefix = p

                            # redo the string view with the capture group
                            view = StringView(reg.groups()[0])

                            invoker = view.get_word()
                            ctx.invoked_with = invoker
                            ctx.prefix = invoked_prefix
                            ctx.view = view
                            ctx.command = self.all_commands.get(
                                reg.groups()[0])
                            return ctx
                    else:
                        # regex has highest priority or something idk
                        # what I'm doing help
                        continue

            # No prefix found, use the branch below
            prefix = [p[0] for p in prefix if not p[1]]
            invoked_prefix = discord.utils.find(view.skip_string, prefix)
            if invoked_prefix is None:
                return ctx
        else:
            invoked_prefix = discord.utils.find(view.skip_string, prefix)
            if invoked_prefix is None:
                return ctx

        invoker = view.get_word()
        ctx.invoked_with = invoker
        ctx.view = view
        ctx.prefix = invoked_prefix
        ctx.command = self.all_commands.get(invoker)
        return ctx

    async def getPrefix(self, bot, msg):
        return commands.when_mentioned_or(*self.prefix)(bot, msg)

    async def on_ready(self):
        app_info = await self.application_info()
        self.invite_url = dutils.oauth_url(app_info.id)
        self.uptime = datetime.datetime.utcnow()
        print(
            f'Logged in as {self.user.name}\nBot invite link: {self.invite_url}')
        # await self.change_presence(game=discord.Game(name=f'{self.prefix[0][0]}help | Version {self.version}', type=0))
        # it doesn't like setting the game
        self.prefix.append([f'<@{self.user.id}> ', False])
        self.prefix.append([f'<@!{self.user.id}> ', False])
        self.load_extension('extensions.core')

    async def on_message(self, message):
        if message.author.bot:
            return
        if message.author.id in self.config.get('BLOCKED'):
            return
        if re.match(r'^pls (pinghelpers?|helpers|hingpelpers?)', message.content) is not None:
            await self.process_commands(message)
            return
        if message.content.startswith('pls') and message.guild.id in nopls:
            return
        if not permissions.owner_id_check(self, str(message.author.id)) and self.maintenance:
            return
        if message.guild.get_member(asd) and message.content.startswith('pls'):
            return
        if message.content.startswith('eiro'):
            content = message.content.split(' ')[1::]
            content.insert(0, 'erio')
            joined = ' '.join(content)
            return message.channel.send(f'I think you meant to use `{joined}`')
        await self.process_commands(message)

    def init_raven(self):
        print('Now initialising Sentry...')
        self.sentry = raven.Client(self.config['SENTRY'])
        print('Sentry initialised.')

    def init_rethinkdb(self):
        print('Now initialising RethinkDB...')
        dbc = self.config['RETHINKDB']
        try:
            self.conn = r.connect(host=dbc['HOST'], port=dbc['PORT'],
                                  db=dbc['DB'], user=dbc['USERNAME'], password=dbc['PASSWORD'])
            dbs = r.db_list().run(self.conn)
            if self.rdb not in dbs:
                print('Database not present. Creating...')
                r.db_create(self.rdb).run(self.conn)
            tables = r.db(self.rdb).table_list().run(self.conn)
            for i in self.rtables:
                if i not in tables:
                    print(f'Table {i} not found. Creating...')
                    r.table_create(i).run(self.conn)
        except Exception as e:
            print('RethinkDB init error!\n{}: {}'.format(type(e).__name__, e))
            sys.exit(1)
        print('RethinkDB initialisation successful.')

    def find_command(self, cmdname: str):
        for i in self.commands:
            if i.name == cmdname:
                return i
        return False

    async def get_settings(self, g):
        exists = (lambda: list(r.table('settings').filter(
            lambda a: a['guild'] == str(g.id)).run(self.conn)) != [])()
        if not exists:
            return None
        settings = list(r.table('settings').filter(
            lambda a: a['guild'] == str(g.id)).run(self.conn))[0]
        return settings


bot = Bot()


@bot.listen("on_command_error")
async def on_command_error(ctx, exception):
    if isinstance(exception, commands_errors.MissingRequiredArgument):
        await ctx.send("You are missing required arguments.")

    elif isinstance(exception, permissions.WrongRole):
        await ctx.send(
            f"\u274C You must be a(n) {exception}.",
            delete_after=3)

    elif isinstance(exception, commands_errors.CommandInvokeError):
        exception = exception.original
        _traceback = traceback.format_tb(exception.__traceback__)
        _traceback = ''.join(_traceback)
        error = discord.Embed(
            title="An error has occurred.",
            color=0xFF0000,
            description="This is (probably) a bug. This has been automatically reported, but you may wanna give ry00001#3487 a poke."
        )
        sentry_string = "{} in command {}\nTraceback (most recent call last):\n{}{}: {}".format(type(
            exception).__name__, ctx.command.qualified_name, _traceback, type(exception).__name__, exception)
        print(sentry_string)
        error.add_field(name="`{}` in command `{}`".format(type(exception).__name__, ctx.command.qualified_name),
                        value="```py\nTraceback (most recent call last):\n{}{}: {}```".format(_traceback, type(exception).__name__, exception))
        if bot.do_sentry:
            ctx.bot.sentry.captureMessage(sentry_string)
        await ctx.send(embed=error)

    elif isinstance(exception, commands_errors.CommandOnCooldown):
        await ctx.send('This command is on cooldown. You can use this command in `{0:.2f}` seconds.'.format(exception.retry_after))

    else:
        ctx.send(exception)


bot.run(bot.config["BOT_TOKEN"])
