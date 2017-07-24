from discord.ext import commands
from discord.ext.commands import errors as commands_errors
from discord import utils as dutils
import traceback
import json
import redis

with open("config.json") as f:
    config = json.load(f)

token = config.get('BOT_TOKEN')
prefix = config.get('BOT_PREFIX')

redis_host = 'localhost'
redis_port = 6379
redis_db = 0

try:
    redis_conn = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
except:
    print('Failed to connect to Redis.')
    exit(2)


class Bot(commands.Bot):
    def __init__(self, command_prefix, redis, **options):
        super().__init__(command_prefix, **options)
        self.send_command_help = send_cmd_help

    async def on_ready(self):
        app_info = await self.application_info()
        self.invite_url = dutils.oauth_url(app_info.id)
        print('Ready.')
        print(self.invite_url)
        print(self.user.name)

        self.load_extension('extensions.core')

    async def on_command_error(self, exception, context):
        if isinstance(exception, commands_errors.MissingRequiredArgument):
            await self.send_command_help(context)
        elif isinstance(exception, commands_errors.CommandInvokeError):
            exception = exception.original
            _traceback = traceback.format_tb(exception.__traceback__)
            _traceback = ''.join(_traceback)
            error = ('`{0}` in command `{1}`: ```py\n'
                     'Traceback (most recent call last):\n{2}{0}: {3}\n```')\
                .format(type(exception).__name__,
                        context.command.qualified_name,
                        _traceback, exception)
            await context.send(error)
        elif isinstance(exception, commands_errors.CommandNotFound):
            pass

    async def on_message(self, message):
        if message.author.bot:
            return
        await self.process_commands(message)


async def send_cmd_help(ctx):
    if ctx.invoked_subcommand:
        _help = await ctx.bot.formatter.format_help_for(ctx,
                                                        ctx.invoked_subcommand)
    else:
        _help = await ctx.bot.formatter.format_help_for(ctx, ctx.command)
    for page in _help:
        await ctx.send(page)


bot = Bot(prefix, redis_conn)
bot.run(token)
