from discord.ext import commands


class WrongRole(commands.CommandError):
    """Thrown when user has wrong role for command."""
    pass


async def is_owner_check(ctx):
    if str(ctx.author.id) in ctx.bot.config.get('OWNERS'):
        return True
    raise WrongRole(message="bot owner")


def is_owner_or_gmod(ctx):
    if (str(ctx.message.author.id) in ctx.bot.config.get('OWNERS')
            or str(ctx.message.author.id) in ctx.bot.config.get('GLOBAL_MODS')):
        return True
    raise WrongRole(message="bot owner or global mod")


def owner_id_check(bot, _id):
    return str(_id) in bot.config.get('OWNERS')


def owner():
    return commands.check(is_owner_check)


def owner_or_gmod():
    return commands.check(is_owner_or_gmod)
