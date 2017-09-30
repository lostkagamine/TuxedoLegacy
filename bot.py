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
from utils import permissions

class Bot(commands.Bot):

    def __init__(self, **options):
        super().__init__(self.getPrefix, **options)
        print('Performing pre-run tasks...')
        self.cmd_help = cmd_help
        self.maintenance = False
        with open("config.json") as f:
            self.config = json.load(f)
            self.prefix = self.config.get('BOT_PREFIX')
        self.remove_command("help")
        self.init_raven()
        self.init_rethinkdb()
        print('Pre-run tasks complete.')

    async def getPrefix(self, bot, msg):
        g = msg.guild
        prefix = self.prefix
        exists = (lambda: list(r.table('settings').filter(
            lambda a: a['guild'] == str(g.id)).run(self.conn)) != [])()
        if exists:
            settings = list(r.table('settings').filter(
                lambda a: a['guild'] == str(g.id)).run(self.conn))[0]
            if 'guild_prefix' in settings.keys():
                prefix = self.prefix.append(settings['guild_prefix'])

        if prefix is None:
            prefix = self.prefix
        return commands.when_mentioned_or(*prefix)(bot, msg)

    async def on_ready(self):
        app_info = await self.application_info()
        self.invite_url = dutils.oauth_url(app_info.id)
        print(
            f'Logged in as {self.user.name}\nBot invite link: {self.invite_url}')
        self.load_extension('extensions.core')

    async def on_message(self, message):
        if message.author.bot:
            return
        if message.author.id in self.config.get('BLOCKED'):
            return
        if not permissions.owner_id_check(str(message.author.id)) and self.maintenance:
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
        except Exception as e:
            print('RethinkDB init error!\n{}: {}'.format(type(e).__name__, e))
            sys.exit(1)
        print('RethinkDB initialisation successful.')


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
        error.add_field(name="`{}` in command `{}`".format(type(exception).__name__, ctx.command.qualified_name),
                        value="```py\nTraceback (most recent call last):\n{}{}: {}```".format(_traceback, type(exception).__name__, exception))
        ctx.bot.sentry.captureMessage(sentry_string)
        await ctx.send(embed=error)
    elif isinstance(exception, commands_errors.CommandOnCooldown):
        await ctx.send('This command is on cooldown. You can use this command in `{0:.2f}` seconds.'.format(exception.retry_after))
    else:
        ctx.send(exception)


@bot.command()
async def help(ctx, command: str = None):
    helptext = await ctx.bot.formatter.format_help_for(ctx, command if command is not None else ctx.bot)
    helptext = helptext[0]
    try:
        await ctx.author.send(helptext)
        await ctx.send(":mailbox_with_mail: Check your DMs.")
    except discord.Forbidden:
        await ctx.send(helptext)

bot.run(bot.config["BOT_TOKEN"])
