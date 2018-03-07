import discord
from discord.ext import commands
import shlex

# aaaa

# hahahahahahahhaahhaa..... hek
def bool_converter(arg):
    arg = str(arg).lower()
    if arg in ["yes", "y", "true", "t", "1", "enable", "on"]:
        return True
    elif arg in ["no", "n", "false", "f", "0", "disable", "off"]:
        return False
    else:
        raise ValueError


class RoleManagement:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['addrole', 'ar'])
    async def addroles(self, ctx, *, args):
        'Adds roles in bulk.'
        members = []
        roles = []
        p = ctx.author.permissions_in(ctx.channel)
        if not p.manage_roles:
            return await ctx.send(':no_entry_sign: Invalid permissions. You need Manage Roles to do this.')
        bp = ctx.me.permissions_in(ctx.channel)
        if not bp.manage_roles:
            return await ctx.send(':no_entry_sign: Give me Manage Roles before doing this.')
        try:
            shlex.split(args)
        except Exception:
            return await ctx.send(':x: | Bad arguments!')
        for i in ctx.message.mentions:
            args = args.replace(f'<@{i.id}>', '')
            args = args.replace(f'<@!{i.id}>', '')
            members.append(i)
        if members == []:
            return await ctx.send(f'One or more members not found.\nExample usage: `{ctx.prefix}{ctx.invoked_with} @ry00001 Members \'Staff Team\'`')
        args = shlex.split(args)
        for i in args:
            r = discord.utils.get(ctx.guild.roles, name=i)
            if not r:
                return await ctx.send(f':x: | One or more roles not found. Use \', not ", for multi-word roles.\nMake sure the capitalisation is correct.\nExample usage: `{ctx.prefix}{ctx.invoked_with} @ry00001 Members \'Staff Team\'`')
            roles.append(r)
        if any([r >= ctx.author.top_role for r in roles]):
            return await ctx.send('You can\'t add roles above or at the same level as you.')
        if any([r >= ctx.me.top_role for r in roles]):
            return await ctx.send('I can\'t add roles above or at the same level as myself.')
        for m in members:
            await m.add_roles(*roles, reason=f'[Roles added by {ctx.author}]')
        await ctx.send('Okay, added.')

    @commands.command(aliases=['removerole', 'rmroles', 'rmrole', 'rr', 'rmr'])
    async def removeroles(self, ctx, *, args):
        'Removes roles in bulk.'
        members = []
        roles = []
        p = ctx.author.permissions_in(ctx.channel)
        if not p.manage_roles:
            return await ctx.send(':no_entry_sign: Invalid permissions. You need Manage Roles to do this.')
        bp = ctx.me.permissions_in(ctx.channel)
        if not bp.manage_roles:
            return await ctx.send(':no_entry_sign: Give me Manage Roles before doing this.')
        try:
            shlex.split(args)
        except Exception:
            return await ctx.send(':x: | Bad arguments!')
        for i in ctx.message.mentions:
            args = args.replace(f'<@{i.id}>', '')
            args = args.replace(f'<@!{i.id}>', '')
            members.append(i)
        if members == []:
            return await ctx.send(f'One or more members not found.\nExample usage: `{ctx.prefix}{ctx.invoked_with} @ry00001 Members \'Staff Team\'`')
        args = shlex.split(args)
        for i in args:
            r = discord.utils.get(ctx.guild.roles, name=i)
            if not r:
                return await ctx.send(f':x: | One or more roles not found. Use \', not ", for multi-word roles.\nMake sure the capitalisation is correct.\nExample usage: `{ctx.prefix}{ctx.invoked_with} @ry00001 Members \'Staff Team\'`')
            roles.append(r)
        if any([r >= ctx.author.top_role for r in roles]):
            return await ctx.send('You can\'t remove roles above or at the same level as you.')
        if any([r >= ctx.me.top_role for r in roles]):
            return await ctx.send('I can\'t remove roles above or at the same level as myself.')
        for m in members:
            await m.remove_roles(*roles, reason=f'[Roles removed by {ctx.author}]')
        await ctx.send('Okay, removed.')

    @commands.has_permissions(manage_roles=True)
    @commands.command()
    async def createrole(self, ctx, *, name: str):
        """Creates a role with the specified name"""
        try:
            await ctx.guild.create_role(name=name, reason="Created by {}".format(ctx.author), permissions=ctx.guild.default_role.permissions)
            await ctx.send("Successfully created a role named `{}`".format(name))
        except discord.errors.Forbidden:
            await ctx.send("I do not have the `Manage Roles` permission")

    @commands.has_permissions(manage_roles=True)
    @commands.command()
    async def deleterole(self, ctx, *, name: str):
        """Deletes the role with the specified name"""
        role = discord.utils.get(ctx.guild.roles, name=name)
        if role is None:
            await ctx.send("No role was found on this server with the name of `{}`".format(name))
            return
        try:
            await role.delete(reason="Deleted by {}".format(ctx.author))
            await ctx.send("Successfully deleted the role named `{}`".format(name))
        except discord.errors.Forbidden:
            if role.position == ctx.me.top_role.position:
                await ctx.send("I cannot delete my highest role")
            elif role.position > ctx.me.top_role.position:
                await ctx.send("I cannot delete that role because it is higher than my highest role")
            else:
                await ctx.send("I do not have the `Manage Roles` permission")

    @commands.has_permissions(manage_roles=True)
    @commands.command()
    async def editrole(self, ctx, type: str, value: str, *, name: str):
        """Edits a role with the specified name"""
        role = discord.utils.get(ctx.guild.roles, name=name)
        if role is None:
            await ctx.send("No role was found on this server with the name of `{}`".format(name))
            return
        if type == "color":
            if value != "remove":
                try:
                    color = discord.Color(value=int(value.strip("#"), 16))
                except:
                    await ctx.send("`{}` is not a valid color. Make sure you are using a hex color! (Ex: #FF0000)".format(value))
                    return
            else:
                color = discord.Color.default()
            try:
                await role.edit(reason="Edited by {}".format(ctx.author), color=color)
                await ctx.send("Successfully edited the role named `{}`".format(name))
            except discord.errors.Forbidden:
                if role.position == ctx.me.top_role.position:
                    await ctx.send("I cannot edit my highest role")
                elif role.position > ctx.me.top_role.position:
                    await ctx.send("I cannot edit that role because it is higher than my highest role")
                else:
                    await ctx.send("I do not have the `Manage Roles` permission")
            except discord.errors.NotFound:
                # Don't ask, for some reason if the role is higher than the bot's highest role it returns a NotFound 404 error
                await ctx.send("That role is higher than my highest role")
        elif type == "permissions":
            try:
                perms = discord.Permissions(permissions=int(value))
            except:
                await ctx.send("`{}` is not a valid permission number! If you need help finding the permission number, then go to <https://discordapi.com/permissions.html> for a permission calculator!".format(value))
                return
            try:
                await role.edit(reason="Edited by {}".format(ctx.author), permissions=perms)
                await ctx.send("Successfully edited the role named `{}`".format(name))
            except discord.errors.Forbidden:
                await ctx.send("I either do not have the `Manage Roles` permission")
            except discord.errors.NotFound:
                await ctx.send("That role is higher than my highest role")
        elif type == "position":
            try:
                pos = int(value)
            except:
                await self.bot.send_message(ctx.channel, "`" + value + "` is not a valid number")
                return
            if pos >= ctx.guild.me.top_role.position:
                await ctx.send("That number is not lower than my highest role's position. My highest role's permission is `{}`".format(ctx.guild.me.top_role.position))
                return
            try:
                if pos <= 0:
                    pos = 1
                await role.edit(reason="Moved by {}".format(ctx.author), position=pos)
                await ctx.send("Successfully edited the role named `{}`".format(name))
            except discord.errors.Forbidden:
                await ctx.send("I do not have the `Manage Roles` permission")
            except discord.errors.NotFound:
                await ctx.send("That role is higher than my highest role")
        elif type == "separate":
            try:
                bool = bool_converter(value)
            except ValueError:
                await ctx.send("`{}` is not a valid boolean".format(value))
                return
            try:
                await role.edit(reason="Edited by {}".format(ctx.author), hoist=bool)
                await ctx.send("Successfully edited the role named `{}`".format(name))
            except discord.errors.Forbidden:
                await ctx.send("I do not have the `Manage Roles` permission or that role is not lower than my highest role.")
        elif type == "mentionable":
            try:
                bool = bool_converter(value)
            except ValueError:
                await ctx.send("`{}` is not a valid boolean".format(value))
                return
            try:
                await role.edit(reason="Edited by {}".format(ctx.author), mentionable=bool)
                await ctx.send("Successfully edited the role named `{}`".format(name))
            except discord.errors.Forbidden:
                await ctx.send("I do not have the `Manage Roles` permission")
            except discord.errors.NotFound:
                await ctx.send("That role is higher than my highest role")
        else:
            await ctx.send("Invalid type specified, valid types are `color`, `permissions`, `position`, `separate`, and `mentionable`")


def setup(bot):
    bot.add_cog(RoleManagement(bot))
