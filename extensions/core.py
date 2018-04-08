import discord
import os
from utils import permissions
from discord.ext import commands
import time
import asyncio
import sys
from utils import exc

class Core:
    def __init__(self, bot):
        self.bot = bot
        self.settings = {
            'extensions': []
        }
        @self.bot.check
        async def no_dms(ctx):
            return ctx.guild is not None
        self.init_extensions()

    def init_extensions(self):
        for ext in os.listdir('extensions'):
            if ext.endswith('.py') and not ext.startswith('core'):
                try:
                    self.bot.load_extension(f'extensions.{ext[:-3]}')
                    self.settings['extensions'].append(f'extensions.{ext[:-3]}')
                except:
                    pass

    @commands.command(aliases=["le"])
    @permissions.owner()
    async def load(self, ctx, name: str):
        """Load an extension into the bot"""
        m = await ctx.send(f'Loading {name}')
        extension_name = 'extensions.{0}'.format(name)
        if extension_name not in self.settings['extensions']:
            try:
                self.bot.load_extension(extension_name)
                self.settings['extensions'].append(extension_name)
                await m.edit(content='Extension loaded.')
            except Exception as e:
                await m.edit(content=f'Error while loading {name}\n`{type(e).__name__}: {e}`')
        else:
            await m.edit(content='Extension already loaded.')

    @commands.command(aliases=["ule", "ul"])
    @permissions.owner()
    async def unload(self, ctx, name: str):
        """Unload an extension from the bot"""
        m = await ctx.send(f'Unloading {name}')
        extension_name = 'extensions.{0}'.format(name)
        if extension_name in self.settings['extensions']:
            self.bot.unload_extension(extension_name)
            self.settings['extensions'].remove(extension_name)
            await m.edit(content='Extension unloaded.')
        else:
            await m.edit(content='Extension not found or not loaded.')

    @commands.command(aliases=["rle", "reloady", "rl"])
    @permissions.owner()
    async def reload(self, ctx, name: str):
        """Reload an extension into the bot"""
        m = await ctx.send(f'Reloading {name}')
        extension_name = 'extensions.{0}'.format(name)
        if extension_name in self.settings['extensions']:
            self.bot.unload_extension(extension_name)
            try:
                self.bot.load_extension(extension_name)
                await m.edit(content='Extension reloaded.')
            except Exception as e:
                self.settings['extensions'].remove(extension_name)
                await m.edit(content=f'Failed to reload extension\n`{type(e).__name__}: {e}`')
        else:
            await m.edit(content='Extension isn\'t loaded.')

    @commands.command(aliases=["restart", 'die'])
    @permissions.owner()
    async def reboot(self, ctx):
        """Ends the bot process"""
        await ctx.send("Rebooting...")
        sys.exit(0)

    @commands.command(aliases=["logout", "shutdown"])
    @permissions.owner()
    async def logoff(self, ctx):
        """Logs the bot off Discord"""
        await ctx.send("Shutting down...")
        await self.bot.logout()

    @commands.command()
    async def ping(self, ctx):
        """Throws a ping pong ball at Discord's servers"""
        before = time.monotonic()
        pong = await ctx.send("...")
        after = time.monotonic()
        ping = (after - before) * 1000
        await pong.edit(content="P-pong! ...{}ms... I know, it's pretty slow...".format(int(ping)))

    @commands.group()
    async def prefix(self, ctx, param):
        pass
        
    @prefix.command()
    @permissions.owner()
    async def add(self, ctx, prefix:str, regex:bool=False):
        'add prefix'
        if [prefix, regex] in self.bot.prefix:
            return await ctx.send('Prefix already exists!')
        self.bot.prefix.append([prefix, regex])
        await ctx.send('\'k')


    @commands.command()
    @permissions.owner()
    async def error(self, ctx):
        """Causes Erio to throw an error"""
        3/0

    @commands.command()
    @permissions.owner()
    async def alias(self, ctx, _from, to):
        """Adds an alias to a command"""
        _from = _from.replace('\'', '').replace('"', '')
        to = to.replace('\'', '').replace('"', '')
        fromcmd = self.bot.get_command(_from)
        if _from == to:
            return await ctx.send(':x: You cannot register an alias with the same name as the command.')
        if fromcmd == None:
            return await ctx.send(':x: The command that needs to be registered is invalid.')
        if to in self.bot.all_commands:
            return await ctx.send(':x: The command to register is already a thing.')
        self.bot.all_commands[to] = fromcmd
        await ctx.send('Okay. Done.')
    
    @commands.command(hidden=True)
    async def erio(self, ctx):
        await ctx.send('Yes, that\'s me. I think.')

def setup(bot):
    bot.add_cog(Core(bot))