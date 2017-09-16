from discord.ext import commands

owners = ["190544080164487168"]


def is_owner_check(ctx):
    return str(ctx.message.author.id) in owners

def owner_id_check(_id):
    return str(_id) in owners


def owner():
    return commands.check(is_owner_check)
