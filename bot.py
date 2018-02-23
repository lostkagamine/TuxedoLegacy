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
import sys
import datetime
from utils import permissions
nopls = [110373943822540800]

asd = 236726289665490944 # Automatic Sink Detection (tm)

class Bot(commands.Bot):

    def __init__(self, **options):
        super().__init__(self.getPrefix, **options)
        print('Performing pre-run tasks...')
        self.cmd_help = cmd_help
        self.maintenance = False
        with open("config.json") as f:
            self.config = json.load(f)
            self.prefix = self.config.get('BOT_PREFIX')
            self.version = self.config.get('VERSION')
        self.remove_command("help")
        self.init_raven()
        self.rdb = self.config['RETHINKDB']['DB']
        self.rtables = ['gbans', 'settings', 'modlog', 'tempbans', 'starboard', 'warnings']
        self.init_rethinkdb()
        print('Pre-run tasks complete.')

    async def getPrefix(self, bot, msg):
        return commands.when_mentioned_or(*self.prefix)(bot, msg)

    async def on_ready(self):
        app_info = await self.application_info()
        self.invite_url = dutils.oauth_url(app_info.id)
        self.uptime = datetime.datetime.utcnow()
        print(
            f'Logged in as {self.user.name}\nBot invite link: {self.invite_url}')
        await self.change_presence(game=discord.Game(name=f'{self.prefix[0]}help | Version {self.version}', type=0))
        self.load_extension('extensions.core')

    async def on_message(self, message):
        if message.author.bot:
            return
        if message.author.id in self.config.get('BLOCKED'):
            return
        if message.content.startswith('pls') and message.guild.id in nopls:
            return
        if not permissions.owner_id_check(self, str(message.author.id)) and self.maintenance:
            return
        if message.guild.get_member(asd) and message.content.startswith('pls'):
            return
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

    def find_command(self, cmdname:str):
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



async def cmd_help(ctx):
    if ctx.invoked_subcommand:
        _help = await ctx.bot.formatter.format_help_for(ctx,
                                                        ctx.invoked_subcommand)
    else:
        _help = await ctx.bot.formatter.format_help_for(ctx, ctx.command)
    for page in _help:
        await ctx.send(page)

bot = Bot()


@bot.listen("on_command_error")
async def on_command_error(ctx, exception):
    if isinstance(exception, commands_errors.MissingRequiredArgument):
        await cmd_help(ctx)
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
        ctx.bot.sentry.captureMessage(sentry_string)
        await ctx.send(embed=error)
    elif isinstance(exception, commands_errors.CommandOnCooldown):
        await ctx.send('This command is on cooldown. You can use this command in `{0:.2f}` seconds.'.format(exception.retry_after))
    else:
        ctx.send(exception)


@bot.command(aliases=['man'])
async def help(ctx, command: str = None):
    if ctx.prefix == "pls " and ctx.invoked_with == "help":
        return
    cmd = ctx.bot.find_command(command)
    helptext = await ctx.bot.formatter.format_help_for(ctx, cmd if cmd is not False else ctx.bot)
    helptext = helptext[0]
    try:
        await ctx.author.send(helptext)
        await ctx.send(":mailbox_with_mail: Check your DMs.")
    except discord.Forbidden:
        await ctx.send(helptext)

bot.run(bot.config["BOT_TOKEN"])
