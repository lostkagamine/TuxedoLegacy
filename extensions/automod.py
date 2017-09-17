import discord
from discord.ext import commands
import rethinkdb as r
import re

regex = r"(?:discord(?:(?:\.|.?dot.?)gg|app(?:\.|.?dot.?)com\/invite)\/(([\w]{1,}|[a-zA-Z0-9]{1,})))"


class AutoMod:
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.conn

        @bot.listen('on_message')
        async def on_message(msg):
            if isinstance(msg.channel, discord.DMChannel) or isinstance(msg.channel, discord.GroupChannel):
                return

            exists = (lambda: list(r.table('settings').filter(
                lambda a: a['guild'] == str(msg.guild.id)).run(self.conn)) != [])()
            if not exists:
                return
            # we know the guild has an entry in the settings
            settings = list(r.table('settings').filter(
                lambda a: a['guild'] == str(msg.guild.id)).run(self.conn))[0]
            if "enable_automod" not in settings.keys():
                return

            if settings['enable_automod']:
                # do cool stuff
                inv = re.search(regex, msg.content)
                if not inv:
                    return

                try:
                    invite = await self.bot.get_invite(inv[0])
                except discord.errors.NotFound:
                    return # Invalid invite

                if invite.guild.id == msg.guild.id:
                    return

                author_perms = msg.author.permissions_in(msg.channel)

                if author_perms.kick_members or author_perms.ban_members or author_perms.administrator:
                    return

                if msg.channel.permissions_for(msg.guild.me).ban_members:
                    await msg.author.ban(reason='Automatic Ban: Advertising', delete_message_days=7)
                    await msg.channel.send(f':hammer: Banned **{str(msg.author)}** automatically for advertising.')
                    return

                if msg.channel.permissions_for(msg.guild.me).manage_messages:
                    await msg.delete()
                    await msg.channel.send(f'{msg.author}, please do not advertise here.')


def setup(bot):
    bot.add_cog(AutoMod(bot))
