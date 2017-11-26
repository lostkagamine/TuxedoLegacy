import discord
from discord.ext import commands
import rethinkdb as r 
import string
from utils import switches

class Projects:
    def __init__(self, bot):
        self.conn = bot.conn
        self.bot = bot

    @commands.group(name='projects', invoke_without_command=True, aliases=['project'])
    async def projects(self, ctx, param):
        raise commands.errors.MissingRequiredArgument()

    def channelify(self, name):
        whitelist = string.ascii_letters + string.digits + ' '
        return ''.join([i for i in name if i in whitelist]).replace(' ', '_')

    def topicify(self, ctx, project):
        lead = str(ctx.guild.get_member(int(project['lead'])))
        members = ', '.join([str(ctx.guild.get_member(int(i))) for i in project['members']])
        if members == '': members = 'None'
        name = project['name']
        desc = project['description']
        return f'[EXPAND TOPIC]\n**{name}**\nLead: {lead}\n{desc}\nMembers: {members}'

    @projects.command(aliases=['new'])
    async def add(self, ctx, name:str, description:str):
        try:
            projectr = r.table('projects').filter(lambda a: a['guild'] == ctx.guild.id and a['name'] == name).run(self.conn)
            try:
                projectr.next()
                return await ctx.send(':x: A project with this name exists already.')
            except Exception:
                pass
            channel = await ctx.guild.create_text_channel(self.channelify(name))
            meme, other = switches.parse(description)
            hidden = False
            if 'hidden' in meme.keys(): # project hidden
                await channel.set_permissions(ctx.guild.default_role, overwrite=discord.PermissionOverwrite(read_messages=False, send_messages=False))
                await channel.set_permissions(ctx.author, overwrite=discord.PermissionOverwrite(read_messages=True, send_messages=True))
                await channel.set_permissions(ctx.me, overwrite=discord.PermissionOverwrite(read_messages=True, send_messages=True))
                hidden = True
            else:
                await channel.set_permissions(ctx.guild.default_role, overwrite=discord.PermissionOverwrite(send_messages=False))
                await channel.set_permissions(ctx.author, overwrite=discord.PermissionOverwrite(send_messages=True))
                await channel.set_permissions(ctx.me, overwrite=discord.PermissionOverwrite(send_messages=True))
            await channel.edit(topic=f'[EXPAND TOPIC]\n**{name}**\nLead: {ctx.author}\n{description}\nMembers: None')
            await channel.send(f'This channel was created automatically for project **{name}**. Please do not remove it manually. When the project is complete, use `project finish "{name}"`.')
            r.table('projects').insert({
                                       'name': name, 
                                       'channel': str(channel.id),
                                       'lead': str(ctx.author.id),
                                       'members': [],
                                       'guild': str(ctx.guild.id),
                                       'description': description,
                                       'hidden': hidden,
                                       'completed': False
                                       }).run(self.conn)

            await ctx.send(f'Project created! I\'ve created a corresponding channel over at <#{channel.id}>.')

        except discord.Forbidden:
            return await ctx.send(':no_entry_sign: I have to have Manage Channels to be able to perform this action.')

    @projects.command(aliases=['rm', 'delete', 'del'])
    async def remove(self, ctx, name:str):
        try:
            projectr = r.table('projects').filter(lambda a: a['guild'] == ctx.guild.id and a['name'] == name).run(self.conn)
            try:
                project = projectr.next()
            except Exception:
                return await ctx.send(':x: Are you sure this is the right name? This project doesn\'t appear to exist.')
            if str(ctx.author.id) != project['lead']:
                return await ctx.send(':x: Only the project lead can delete this project.')
            # there's gonna be a project and the perms will be valid after this
            channel = ctx.guild.get_channel(int(project['channel']))
            if channel == None: 
                await ctx.send(':x: Has the channel gotten deleted? I\'ll delete the project from my database.')
                r.table('projects').get(project['id']).delete().run(self.conn)
            else:
                await channel.delete(reason='Project deleted.')
                r.table('projects').get(project['id']).delete().run(self.conn)
                await ctx.send('Project deleted.')
        except discord.Forbidden:
            return await ctx.send(':no_entry_sign: I have to have Manage Channels to be able to perform this action.')

    @projects.command(aliases=['add_m', 'new_m', 'new_member'])
    async def add_member(self, ctx, name:str, member:discord.Member):
        try:
            projectr = r.table('projects').filter(lambda a: a['guild'] == ctx.guild.id and a['name'] == name).run(self.conn)
            try:
                project = projectr.next()
            except Exception:
                return await ctx.send(':x: Are you sure this is the right name? This project doesn\'t appear to exist.')
            if str(ctx.author.id) != project['lead']:
                return await ctx.send(':x: Only the project lead can add members to this project.')
            if str(member.id) in project['members']:
                return await ctx.send(':x: This member is already in the project.')
            project['members'].append(str(member.id))
            channel = ctx.guild.get_channel(int(project['channel']))
            if project['hidden']:
                await channel.set_permissions(member, overwrite=discord.PermissionOverwrite(read_messages=True, send_messages=True))
            else:
                await channel.set_permissions(member, overwrite=discord.PermissionOverwrite(send_messages=True))
            await channel.edit(topic=self.topicify(ctx, project))
            r.table('projects').filter(lambda a: a['guild'] == ctx.guild.id and a['name'] == name).update({'members': project['members']}).run(self.conn)
            await ctx.send(f'{str(member)} has been added to the project.')
        except discord.Forbidden:
            return await ctx.send(':no_entry_sign: I have to have Manage Channels to be able to perform this action.')
    
    @projects.command(aliases=['rm_member', 'del_member', 'rm_m', 'del_m'])
    async def remove_member(self, ctx, name:str, member:discord.Member):
        try:
            projectr = r.table('projects').filter(lambda a: a['guild'] == ctx.guild.id and a['name'] == name).run(self.conn)
            try:
                project = projectr.next()
            except Exception:
                return await ctx.send(':x: Are you sure this is the right name? This project doesn\'t appear to exist.')
            if str(ctx.author.id) != project['lead']:
                return await ctx.send(':x: Only the project lead can remove members from this project.')
            if str(member.id) not in project['members']:
                return await ctx.send(':x: This member isn\'t even in the project.')
            project['members'].remove(str(member.id))
            channel = ctx.guild.get_channel(int(project['channel']))
            if project['hidden']:
                await channel.set_permissions(member, overwrite=discord.PermissionOverwrite(read_messages=False, send_messages=False))
            else:
                await channel.set_permissions(member, overwrite=discord.PermissionOverwrite(send_messages=False))
            await channel.edit(topic=self.topicify(ctx, project))
            r.table('projects').filter(lambda a: a['guild'] == ctx.guild.id and a['name'] == name).update({'members': project['members']}).run(self.conn)
            await ctx.send(f'{str(member)} has been removed from the project.')
        except discord.Forbidden:
            return await ctx.send(':no_entry_sign: I have to have Manage Channels to be able to perform this action.')

    @projects.command(aliases=['transfer'])
    async def transfer_lead(self, ctx, name:str, member:discord.Member):
        try:
            projectr = r.table('projects').filter(lambda a: a['guild'] == ctx.guild.id and a['name'] == name).run(self.conn)
            try:
                project = projectr.next()
            except Exception:
                return await ctx.send(':x: Are you sure this is the right name? This project doesn\'t appear to exist.')
            if str(ctx.author.id) != project['lead']:
                return await ctx.send(':x: Only the project lead can transfer leadership to another member, obviously.')
            if str(member.id) not in project['members']:
                return await ctx.send(':x: This member isn\'t in the project. Add them first.')
            await ctx.send(f'Are you sure you want to transfer project lead to {str(member)}? Say `yes` or `y` to confirm, say anything else to cancel.')
            msg = await self.bot.wait_for('message', check=lambda a: a.channel == ctx.channel and a.author == ctx.author)
            if msg.content.lower() not in ['y', 'yes']: return await ctx.send('Cancelled operation.')
            project['lead'] = str(member.id)
            project['members'].remove(str(member.id))
            project['members'].append(str(ctx.author.id))
            channel = ctx.guild.get_channel(int(project['channel']))
            await channel.edit(topic=self.topicify(ctx, project))
            r.table('projects').filter(lambda a: a['guild'] == ctx.guild.id and a['name'] == name).update({'lead': project['lead'], 'members': project['members']}).run(self.conn)
            await ctx.send(f'You have transferred project lead to {str(member)} successfully.')
        except discord.Forbidden:
            return await ctx.send(':no_entry_sign: I have to have Manage Channels to be able to perform this action.')

    @projects.command(aliases=['complete'])
    async def finish(self, ctx, name:str):
        try:
            projectr = r.table('projects').filter(lambda a: a['guild'] == ctx.guild.id and a['name'] == name).run(self.conn)
            try:
                project = projectr.next()
            except Exception:
                return await ctx.send(':x: Are you sure this is the right name? This project doesn\'t appear to exist.')
            if str(ctx.author.id) != project['lead']:
                return await ctx.send(':x: Only the project lead can mark a project as finished and archive it.')
            await ctx.send(f'Are you sure you want to mark this project as finished? You won\'t be able to send here anymore.\nSay `yes` or `y` to confirm, say anything else to cancel.')
            msg = await self.bot.wait_for('message', check=lambda a: a.channel == ctx.channel and a.author == ctx.author)
            if msg.content.lower() not in ['y', 'yes']: return await ctx.send('Cancelled operation.')
            channel = ctx.guild.get_channel(int(project['channel']))
            project['completed'] = True
            await channel.edit(name=f'{str(channel)}-archived', topic=self.topicify(ctx, project))
            for i in channel.overwrites:
                await channel.set_permissions(i[0], overwrite=discord.PermissionOverwrite(send_messages=False))
            r.table('projects').filter(lambda a: a['guild'] == ctx.guild.id and a['name'] == name).update({'completed': True}).run(self.conn)
            await ctx.send('Project marked as completed successfully. This channel has been archived.')
        except discord.Forbidden:
            return await ctx.send(':no_entry_sign: I have to have Manage Channels to be able to perform this action.')


def setup(bot):
    bot.add_cog(Projects(bot))
