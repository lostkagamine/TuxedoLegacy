import aiohttp
import json
import logging

log = logging.getLogger(__name__)

DBL_API = 'https://discordbots.org/api'
DISCORD_BOTS_API = 'https://bots.discord.pw/api'


class ServerCounts:
    """Might update the servercounts."""

    def __init__(self, bot):
        self.bot = bot

    async def update(self):
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
            log.info(
                f'DBL: posting {dbots_count} count with status {resp.status}')
            
#########################################################################################################################

        dbl_counts = json.dumps({
            'server_count': guild_count
        })
        token = bot.config.get('DBL_TOKEN', None)

        headers = {
            'authorization': token,
            'content-type': 'application/json'
        }

        url1 = f'{DBL_API}/bots/{self.bot.user.id}/stats'
        async with self.bot.session.post(url1, data=dbl_counts, headers=headers) as resp:
            log.info(
                f'DBL: posting {dbl_counts} count with status {resp.status}')

    async def on_guild_join(self, guild):
        await self.update()

    async def on_guild_remove(self, guild):
        await self.update()

    async def on_ready(self):
        await self.update()


def setup(bot):
    bot.add_cog(ServerCounts(bot))
