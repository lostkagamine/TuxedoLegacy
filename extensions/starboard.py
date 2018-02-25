import discord
from discord.ext import commands
from utils import database, randomness
import datetime, random
import rethinkdb as rethink

# Tuxedo starboard module
# Don't steal pls, it's FOSS but don't thanks.
# very basic, will expand later:tm:

# thanks taci and/or /r/unixporn for using my bot


# yes seriously

class Starboard:
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.conn

    def star_type(self, count):  # BORROWED from RoboDanny
        if 5 > count >= 0:
            return '\N{WHITE MEDIUM STAR}'
        elif 10 > count >= 5:
            return '\N{GLOWING STAR}'
        elif 25 > count >= 10:
            return '\N{DIZZY SYMBOL}'
        else:
            return '\N{SPARKLES}'

    async def process_star(self, r, u):
        name = (r.emoji if type(r.emoji) == str
                else r.emoji.name)  # may as well
        count = r.count
        settings = database.get_settings(
            self.conn, r.message.guild)  # grab me all the settings
        if not settings:
            return  # oops, no settings
        if 'starboard_channel' not in settings.keys():
            return  # oops, no sb channel
        if r.message.author == u:
            return  # no heckin self stars
        min_count = database.check_setting(
            self.conn, r.message.guild, 'starboard_min_count') or 1
        sb_name = database.check_setting(
            self.conn, r.message.guild, 'starboard_emote') or '⭐'
        channel = database.check_setting(
            self.conn, r.message.guild, 'starboard_channel')
        channel = r.message.guild.get_channel(
            int(channel))  # get proper channel
        if r.message.channel == channel:
            return

        star_entry = list(
            rethink.table("starboard")
            .filter({"message_id": str(r.message.id)})
            .run(self.conn))

        if channel is None:
            return  # no more starboard channel, don't wanna throw an exception
        if name == sb_name:
            print(count)
            if count >= min_count:
                e = discord.Embed(colour=r.message.author.color)
                e.set_author(
                    name=str(r.message.author.display_name),
                    icon_url=r.message.author.avatar_url_as(format='png'))
                e.description = r.message.content
                e.timestamp = datetime.datetime.utcnow()
                if r.message.attachments:
                    e.set_image(url=r.message.attachments[0].url)

                # Set the custom star for the first 5 stars a message gets, then switch to normal behavior.
                if sb_name is not '⭐' and count < 5:
                    fallback = f'{sb_name} **{count}** <#{r.message.channel.id}>'
                else:
                    fallback = f'{self.star_type(count)} **{count}** <#{r.message.channel.id}>'

                if not star_entry:
                    star_msg = await channel.send(fallback, embed=e)
                    star_entry = {
                        "message_id": str(r.message.id),
                        "starboard_id": str(star_msg.id)
                    }
                    return rethink \
                        .table("starboard") \
                        .insert(star_entry) \
                        .run(self.conn)
                    
                else:
                    try:
                        star_msg = await channel.get_message(
                            star_entry[0]["starboard_id"])
                        return await star_msg.edit(content=fallback, embed=e)
                    except discord.errors.NotFound:
                        new_star_msg = await channel.send(fallback, embed=e)
                        return rethink \
                            .table("starboard") \
                            .filter({"message_id": str(r.message.id)}) \
                            .update({"starboard_id": str(new_star_msg.id)}) \
                            .run(self.conn)
            elif star_entry:
                try:
                    star_msg = await channel.get_message(
                        star_entry[0]["starboard_id"])
                    return await star_msg.delete()
                except discord.errors.NotFound:
                    return

    async def on_reaction_add(self, r, u):
        return await self.process_star(r, u)

    async def on_reaction_remove(self, r, u):
        return await self.process_star(r, u)


def setup(bot):
    bot.add_cog(Starboard(bot))
