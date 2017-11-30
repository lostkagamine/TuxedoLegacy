from discord.ext import commands

def is_owner_check(ctx):
    return str(ctx.message.author.id) in ctx.bot.config.get('OWNERS')

def owner_id_check(_id):
    return str(_id) in ctx.bot.config.get('OWNERS')


def owner():
    return commands.check(is_owner_check)
