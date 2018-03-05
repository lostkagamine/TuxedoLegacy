#!/usr/bin/env python3

import discord
from discord.ext import commands

# look at this net
class Net(BaseException):
    # that i just found
    @commands.command(pass_context=True)
    async def net(self, ctx, *, msg):
        """net"""
        # when i say go, be ready to throw
        raise Net
        # ...

def setup(bot):
    """Set up the extension."""
    bot.add_cog(Net())
