import traceback
import json
from discord.ext import commands
from discord.ext.commands import errors as commands_errors
from discord import utils as dutils

with open("config.json") as f:
    config = json.load(f)

token = config.get('BOT_TOKEN')




class Bot(commands.Bot):

    prefix = config.get('BOT_PREFIX')

    async def getPrefix(self, bot, msg):
        return commands.when_mentioned_or(*self.prefix)(bot, msg)

    def __init__(self, **options):
        super().__init__(self.getPrefix, **options)
        self.cmd_help = cmd_help

    async def on_ready(self):
        app_info = await self.application_info()
        self.invite_url = dutils.oauth_url(app_info.id)
        print(f'Logged in as {self.user.name}\nBot invite link: {self.invite_url}')
        self.load_extension('extensions.core')

    async def on_message(self, message):
        if message.author.bot:
            return
        await self.process_commands(message)


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
        error = ('`{0}` in command `{1}`: ```py\n'
                 'Traceback (most recent call last):\n{2}{0}: {3}\n```')\
                 .format(type(exception).__name__,
                 ctx.command.qualified_name,
                 _traceback, exception)
        await ctx.send(error)
    elif isinstance(exception, commands_errors.CommandOnCooldown):
        await ctx.send('This command is on cooldown. You can use this command in `{0:.2f}` seconds.'.format(exception.retry_after))
    else:
        ctx.send(exception)

bot.run(token)
