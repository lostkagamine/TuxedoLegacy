# Based off repl from RDanny by Danny.
# Will fail if the bot does not have embed permissions.
# Embed designed and implemented by taciturasa.
# Released under the MIT License.
#
# The MIT License (MIT)
#
# Copyright (c) 2015 Rapptz
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import discord
from discord.ext import commands
import collections
import aiohttp
import inspect
import traceback
from contextlib import redirect_stdout
from utils import permissions
import io
import datetime


class EmbedShell():
    def __init__(self, bot):
        self.bot = bot
        self.repl_sessions = {}
        self.repl_embeds = {}
        self.aioclient = aiohttp.ClientSession()
        self.twitter = '@atteybot'

    def cleanup_code(self, content):
        '''Automatically removes code blocks from the code.'''
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    def get_syntax_error(self, err):
        '''Returns SyntaxError formatted for repl reply.'''
        return '```py\n{0.text}{1:>{0.offset}}\n{2}: {0}```'.format(
            err,
            '^',
            type(err).__name__)

    async def post_to_hastebin(self, string):
        '''Posts a string to hastebin.'''
        url = "https://hastebin.com/documents"
        data = string.encode('utf-8')
        async with self.aioclient.post(url=url, data=data) as haste_response:
            print(haste_response)
            haste_key = (await haste_response.json())['key']
            haste_url = f"http://hastebin.com/{haste_key}"
        return haste_url

    @commands.group(name='shell',
                    aliases=['ipython', 'repl',
                             'longexec', 'core', 'overkill'],
                    pass_context=True,
                    invoke_without_command=True)
    @permissions.owner()
    async def repl(self, ctx, *, name: str=None):
        '''Head on impact with an interactive python shell.'''
        # TODO Minimize local variables
        # TODO Minimize branches

        session = ctx.message.channel.id

        embed = discord.Embed(
            description="_Enter code to execute or evaluate. "
            "`exit()` or `quit` to exit._",
            timestamp=datetime.datetime.now())

        embed.set_footer(
            text="Interactive Python Shell",
            icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb"
            "/c/c3/Python-logo-notext.svg/1024px-Python-logo-notext.svg.png")

        if name is not None:
            embed.title = name.strip(" ")

        history = collections.OrderedDict()

        variables = {
            'ctx': ctx,
            'bot': self.bot,
            'message': ctx.message,
            'server': ctx.message.guild,
            'channel': ctx.message.channel,
            'author': ctx.message.author,
            'discord': discord,
            '_': None
        }

        if session in self.repl_sessions:
            error_embed = discord.Embed(
                color=15746887,
                description="**Error**: "
                "_Shell is already running in channel._")
            await ctx.send(embed=error_embed)
            return

        shell = await ctx.send(embed=embed)

        self.repl_sessions[session] = shell
        self.repl_embeds[shell] = embed

        while True:
            response = await self.bot.wait_for(
                'message',
                check=lambda m: m.content.startswith('`') and m.author == ctx.author and m.channel == ctx.channel)

            cleaned = self.cleanup_code(response.content)
            shell = self.repl_sessions[session]

            # Regular Bot Method
            try:
                await ctx.message.channel.get_message(
                    self.repl_sessions[session].id)
            except discord.NotFound:
                new_shell = await ctx.send(embed=self.repl_embeds[shell])
                self.repl_sessions[session] = new_shell

                embed = self.repl_embeds[shell]
                del self.repl_embeds[shell]
                self.repl_embeds[new_shell] = embed

                shell = self.repl_sessions[session]

            try:
                await response.delete()
            except discord.Forbidden:
                pass

            if len(self.repl_embeds[shell].fields) >= 7:
                self.repl_embeds[shell].remove_field(0)

            if cleaned in ('quit', 'exit', 'exit()'):
                self.repl_embeds[shell].color = 16426522

                if self.repl_embeds[shell].title is not discord.Embed.Empty:
                    history_string = "History for {}\n\n\n".format(
                        self.repl_embeds[shell].title)
                else:
                    history_string = "History for latest session\n\n\n"

                for item in history.keys():
                    history_string += ">>> {}\n{}\n\n".format(
                        item,
                        history[item])

                haste_url = await self.post_to_hastebin(history_string)
                return_msg = "[`Leaving shell session. "\
                    "History hosted on hastebin.`]({})".format(
                        haste_url)

                self.repl_embeds[shell].add_field(
                    name="`>>> {}`".format(cleaned),
                    value=return_msg,
                    inline=False)

                await self.repl_sessions[session].edit(
                    embed=self.repl_embeds[shell])

                del self.repl_embeds[shell]
                del self.repl_sessions[session]
                return

            executor = exec
            if cleaned.count('\n') == 0:
                # single statement, potentially 'eval'
                try:
                    code = compile(cleaned, '<repl session>', 'eval')
                except SyntaxError:
                    pass
                else:
                    executor = eval

            if executor is exec:
                try:
                    code = compile(cleaned, '<repl session>', 'exec')
                except SyntaxError as err:
                    self.repl_embeds[shell].color = 15746887

                    return_msg = self.get_syntax_error(err)

                    history[cleaned] = return_msg

                    if len(cleaned) > 800:
                        cleaned = "<Too big to be printed>"
                    if len(return_msg) > 800:
                        haste_url = await self.post_to_hastebin(return_msg)
                        return_msg = "[`SyntaxError too big to be printed. "\
                            "Hosted on hastebin.`]({})".format(
                                haste_url)

                    self.repl_embeds[shell].add_field(
                        name="`>>> {}`".format(cleaned),
                        value=return_msg,
                        inline=False)

                    await self.repl_sessions[session].edit(
                        embed=self.repl_embeds[shell])
                    continue

            variables['message'] = response

            fmt = None
            stdout = io.StringIO()

            try:
                with redirect_stdout(stdout):
                    result = executor(code, variables)
                    if inspect.isawaitable(result):
                        result = await result
            except Exception as err:
                self.repl_embeds[shell].color = 15746887
                value = stdout.getvalue()
                fmt = '```py\n{}{}\n```'.format(
                    value,
                    traceback.format_exc())
            else:
                self.repl_embeds[shell].color = 4437377

                value = stdout.getvalue()

                if result is not None:
                    fmt = '```py\n{}{}\n```'.format(
                        value,
                        result)

                    variables['_'] = result
                elif value:
                    fmt = '```py\n{}\n```'.format(value)

            history[cleaned] = fmt

            print("got this far as well")
            if len(cleaned) > 800:
                cleaned = "<Too big to be printed>"

            try:
                if fmt is not None:
                    if len(fmt) >= 800:
                        haste_url = await self.post_to_hastebin(fmt)
                        self.repl_embeds[shell].add_field(
                            name="`>>> {}`".format(cleaned),
                            value="[`Content too big to be printed. "
                            "Hosted on hastebin.`]({})".format(
                                       haste_url),
                            inline=False)

                        await self.repl_sessions[session].edit(
                            embed=self.repl_embeds[shell])
                    else:
                        self.repl_embeds[shell].add_field(
                            name="`>>> {}`".format(cleaned),
                            value=fmt,
                            inline=False)

                        await self.repl_sessions[session].edit(
                            embed=self.repl_embeds[shell])
                else:
                    self.repl_embeds[shell].add_field(
                        name="`>>> {}`".format(cleaned),
                        value="`Empty response, assumed successful.`",
                        inline=False)

                    await self.repl_sessions[session].edit(
                        embed=self.repl_embeds[shell])

            except discord.Forbidden:
                pass

            except discord.HTTPException as err:
                error_embed = discord.Embed(
                    color=15746887,
                    description='**Error**: _{}_'.format(err))
                await ctx.send(embed=error_embed)

    @repl.command(name='jump',
                  aliases=['hop', 'pull', 'recenter', 'whereditgo'],
                  pass_context=True)
    @permissions.owner()
    async def _repljump(self, ctx):
        '''Brings the shell back down so you can see it again.'''

        session = ctx.message.channel.id

        if session not in self.repl_sessions:
            error_embed = discord.Embed(
                color=15746887,
                description="**Error**: _No shell running in channel._")
            await ctx.send(embed=error_embed)
            return

        shell = self.repl_sessions[session]
        embed = self.repl_embeds[shell]

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        try:
            await shell.delete()
        except discord.errors.NotFound:
            pass
        new_shell = await ctx.send(embed=embed)

        self.repl_sessions[session] = new_shell

        del self.repl_embeds[shell]
        self.repl_embeds[new_shell] = embed

    @repl.command(name='clear',
                  aliases=['clean', 'purge', 'cleanup',
                           'ohfuckme', 'deletthis'],
                  pass_context=True)
    @permissions.owner()
    async def _replclear(self, ctx):
        '''Clears the fields of the shell and resets the color.'''

        session = ctx.message.channel.id

        if session not in self.repl_sessions:
            error_embed = discord.Embed(
                color=15746887,
                description="**Error**: _No shell running in channel._")
            await ctx.send(embed=error_embed)
            return

        shell = self.repl_sessions[session]

        self.repl_embeds[shell].color = discord.Color.default()
        self.repl_embeds[shell].clear_fields()

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        await shell.edit(embed=self.repl_embeds[shell])


def setup(bot):
    bot.add_cog(EmbedShell(bot))
