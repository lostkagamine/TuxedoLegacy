import aiohttp
import json
from discord.ext import commands

DBL_API = 'https://discordbots.org/api'
DISCORD_BOTS_API = 'https://bots.discord.pw/api'


class ManualSC:
    """manual shit for updating the servercounts."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def sourceisgay(self, ctx):
        guild_count = len(self.bot.guilds)
        dbots_count = json.dumps({
            'server_count': guild_count
        })
        token = self.bot.config.get("DBOTS_TOKEN", None)

        headers = {
            'authorization': token,
            'content-type': 'application/json'
        }

        url = f'{DISCORD_BOTS_API}/bots/{self.bot.user.id}/stats'
        async with self.bot.session.post(url, data=dbots_count, headers=headers) as resp:
            ctx.send(
                f'DBL: posting {dbots_count} count with status {resp.status}')

######################################################################################################

        dbl_counts = json.dumps({
            'server_count': guild_count
        })
        token = self.bot.config.get("dbl", None)

        headers = {
            'authorization': token,
            'content-type': 'application/json'
        }

        url1 = f'{DBL_API}/bots/{self.bot.user.id}/stats'
        async with self.bot.session.post(url1, data=dbl_counts, headers=headers) as resp:
            ctx.send(
                f'DBL: posting {dbl_counts} count with status {resp.status}')


def setup(bot):
    bot.add_cog(ManualSC(bot))
