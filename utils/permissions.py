from discord.ext import commands

bot = None

def is_owner_check(ctx):    
    bot = ctx.bot
    return str(ctx.message.author.id) in ctx.bot.config.get('OWNERS')

def owner_id_check(bot, _id):
    return str(_id) in bot.config.get('OWNERS')


def owner():
    return commands.check(is_owner_check)

