from discord.ext import commands


def is_owner_check(ctx):
    return str(ctx.message.author.id) in ['190544080164487168', "180093157554388993", "163948331956043776"]


def owner():
    return commands.check(is_owner_check)
