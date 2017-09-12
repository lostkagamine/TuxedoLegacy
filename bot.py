import traceback
import json
import discord
from discord.ext import commands
from discord.ext.commands import errors as commands_errors
from discord import utils as dutils
import random
import asyncio
import raven

class Bot(commands.Bot):

    def __init__(self, **options):
        super().__init__(self.getPrefix, **options)
        self.cmd_help = cmd_help
        with open("config.json") as f:
            self.config = json.load(f)
            self.prefix = self.config.get('BOT_PREFIX')
        self.remove_command("help")
        self.init_raven()

    async def getPrefix(self, bot, msg):
        return commands.when_mentioned_or(*self.prefix)(bot, msg)

    async def on_ready(self):
        app_info = await self.application_info()
        self.invite_url = dutils.oauth_url(app_info.id)
        print(f'Logged in as {self.user.name}\nBot invite link: {self.invite_url}')
        self.load_extension('extensions.core')

    async def on_message(self, message):
        if message.author.bot:
            return
        if message.author.id in self.config.get('BLOCKED'): return
        await self.process_commands(message)

    def init_raven(self):
        print('Now initialising Sentry...')
        self.sentry = raven.Client(self.config['SENTRY'])
        print('Sentry initialised.')


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
        # error = ('**An error has occurred.**\n\n`{0}` in command `{1}`: ```py\n'
        #          'Traceback (most recent call last):\n{2}{0}: {3}\n```\n\nThis is (probably) a bug. You may want to join https://discord.gg/KEcme4H to report the issue and hopefully get it fixed.')\
        #          .format(type(exception).__name__,
        #          ctx.command.qualified_name,
        #          _traceback, exception)
        error = discord.Embed(
            title="An error has occurred.",
            color=0xFF0000,
            description="This is (probably) a bug. You may want to join https://discord.gg/KEcme4H to report it and get it fixed."
        )
        error.add_field(name="`{}` in command `{}`".format(type(exception).__name__, ctx.command.qualified_name), value="```py\nTraceback (most recent call last):\n{}{}: {}```".format(_traceback, type(exception).__name__, exception))
        await ctx.send(embed=error)
    elif isinstance(exception, commands_errors.CommandOnCooldown):
        await ctx.send('This command is on cooldown. You can use this command in `{0:.2f}` seconds.'.format(exception.retry_after))
    else:
        ctx.send(exception)

@bot.command()
async def help(ctx):
    helptext = await ctx.bot.formatter.format_help_for(ctx, ctx.bot)
    helptext = helptext[0]
    try:
        await ctx.author.send(helptext)
        await ctx.send(":mailbox_with_mail: Check your DMs.")
    except discord.Forbidden:
        await ctx.send(helptext)

bot.run(bot.config["BOT_TOKEN"])
