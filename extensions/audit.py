import aiohttp
import discord
from discord.ext import commands

cleaner = {
    "guild_update": "updated the guild",
    "channel_create": "created channel",
    "channel_update": "updated channel",
    "channel_delete": "deleted channel",
    "overwrite_create": "created channel permission overwrite",
    "overwrite_update": "changed channel permission overwrite",
    "overwrite_delete": "deleted channel permission overwrite",
    "kick": "kicked a member",
    "member_prune": "member prune was triggered",
    "ban": "banned a member",
    "unban": "unbanned a member",
    "member_update": "updated a member",
    "member_role_update": "updated roles for a memeber",
    "role_create": "created a role",
    "role_update": "updated a role",
    "role_delete": "deleted a role",
    "invite_create": "created an invite",
    "invite_update": "updated the invite",
    "invite_delete": "deleted an invite",
    "webhook_create": "created a webhook",
    "webhook_update": "updated the webhook",
    "webhook_delete": "deleted the webhook",
    "emoji_create": "created an emote",
    "emoji_update": "updated an emote",
    "emoji_delete": "deleted an emote",
    "message_delete": "deleted a message"
}


class AuditLogs:

    async def haste_get(self, output):
        with aiohttp.ClientSession() as sess:
            async with sess.post("https://hastebin.com/documents/", data=output, headers={"Content-Type": "text/plain"}) as r:
                r = await r.json()
                return (f"https://hastebin.com/{r['key']}")

    @commands.has_permissions(view_audit_log=True)
    @commands.command()
    async def audit(self, ctx):
        """Audit logs on phone!!"""
        try:
            await ctx.trigger_typing()
            embed = discord.Embed(color=0xB388FF)
            embed.title = f"Audit logs for the {ctx.guild.name}"
            embed.set_footer(
                text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar_url_as(format="png"))
            embed.set_thumbnail(url=ctx.guild.icon_url)
            
            async for entry in ctx.guild.audit_logs(limit=10):
                reason = entry.reason
                if reason:
                    pass
                else:
                    reason = "Not provided"

                embed.add_field(name='User: `{0.user}`, Target: `{0.target}`.'.format(
                    entry), value="Action: `" + cleaner[f"{entry.action.name}"]+"`\n" + f"Reason: {reason}")
            message = []
            async for entry in ctx.guild.audit_logs(limit=100):
                reason = entry.reason
                if reason:
                    pass
                else:
                    reason = "Not provided"

                message.append(
                    f"User: {entry.user}\nAction: " + cleaner[f'{entry.action.name}'] +f".\nTarget: {entry.target}"+ f"\nReason: {reason}\n\n")
            output = "".join(message)
            url = await self.haste_get(output)
            embed.description = f"[See more of the audit log here.]({url})"
            await ctx.send(embed=embed)
        except Exception:
            await ctx.send("I do not have permission to see audit logs :<")


def setup(bot):
    """Set up the extension."""
    bot.add_cog(AuditLogs())
