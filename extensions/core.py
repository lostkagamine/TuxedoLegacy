import discord
import os
from utils import permissions
from discord.ext import commands
import time

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
        """ Load an extension into the bot """
        m = await ctx.send(f'Loading {name}')
        extension_name = 'extensions.{0}'.format(name)
        if extension_name not in self.settings['extensions']:
            try:
                self.bot.load_extension(extension_name)
                self.settings['extensions'].append(extension_name)
                await m.edit(content='Extension loaded.')
            except Exception as e:
                await m.edit(content=f'Error while loading {name}\n`{e}`')
        else:
            await m.edit(content='Extension already loaded.')

    @commands.command(aliases=["ule", "ul"])
    @permissions.owner()
    async def unload(self, ctx, name: str):
        """ Unload an extension from the bot """
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
        """ Reload an extension into the bot """
        m = await ctx.send(f'Reloading {name}')
        extension_name = 'extensions.{0}'.format(name)
        if extension_name in self.settings['extensions']:
            self.bot.unload_extension(extension_name)
            try:
                self.bot.load_extension(extension_name)
                await m.edit(content='Extension reloaded.')
            except Exception as e:
                self.settings['extensions'].remove(extension_name)
                await m.edit(content=f'Failed to reload extension\n{e}')
        else:
            await m.edit(content='Extension isn\'t loaded.')

    @commands.command(aliases=["restart"])
    @permissions.owner()
    async def reboot(self, ctx):
        """ Ends the bot process """
        await ctx.send("Rebooting...")
        quit()

    @commands.command(aliases=["logout", "shutdown"])
    @permissions.owner()
    async def logoff(self, ctx):
        """ Logs the bot off Discord """
        await ctx.send("Shutting down...")
        await self.bot.logout()

    @commands.command()
    async def ping(self, ctx):
        before = time.monotonic()
        pong = await ctx.send("...")
        after = time.monotonic()
        ping = (after - before) * 1000
        await pong.edit(content="`PING discordapp.com {}ms`".format(int(ping)))

    @commands.command(description="Manage those prefixes.")
    @permissions.owner()
    async def prefix(self, ctx, *args): # ported from rybot
        if args == None: return
        if args[0] == "add":
            if args[1] == None:
                await ctx.send("Specify a prefix to add.")
                return
            if args[1] in self.bot.prefix:
                await ctx.send("You've tried to add a duplicate prefix...")
                return
            self.bot.prefix.append(args[1])
            await ctx.send("Added prefix " + args[1])
        elif args[0] == "remove":
            if args[1] == None:
                await ctx.send("Specify a prefix to remove.")
                return
            if not args[1] in self.bot.prefix:
                await ctx.send("You've tried to remove a non-existent prefix...")
                return
            self.bot.prefix.remove(args[1])
            await ctx.send("Removed prefix " + args[1])
        elif args[0] == "list":
            prefixes = "\n".join(self.bot.prefix)
            await ctx.send(f"```\n{prefixes}```")






def setup(bot):
    bot.add_cog(Core(bot))