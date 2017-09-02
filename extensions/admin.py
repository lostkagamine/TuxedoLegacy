import discord
import textwrap
import time
from discord.ext import commands
from utils import permissions
from utils import randomness
import aiohttp
import asyncio

class Admin:
    def __init__(self, bot):
        self.bot = bot
        self._eval = {}

    @commands.command(name="setavy")
    @permissions.owner()
    async def set_avy(self, ctx, *, avy : str):
        async with aiohttp.ClientSession() as sesh:
            async with sesh.get(avy) as r:
                await self.bot.user.edit(avatar=await r.read())
                await ctx.send(":ok_hand:")

    @commands.command(aliases=["ev", "e"])
    @permissions.owner()
    async def eval(self, ctx, *, code: str):
        """Evaluates Python code"""
        if self._eval.get('env') is None:
            self._eval['env'] = {}
        if self._eval.get('count') is None:
            self._eval['count'] = 0

        codebyspace = code.split(" ")
        print(codebyspace)
        silent = False
        if codebyspace[0] == "--silent" or codebyspace[0] == "-s": 
            silent = True
            print("silent mmLol")
            codebyspace = codebyspace[1:]
            code = " ".join(codebyspace)


        self._eval['env'].update({
            'self': self.bot,
            'ctx': ctx,
            'message': ctx.message,
            'channel': ctx.message.channel,
            'guild': ctx.message.guild,
            'author': ctx.message.author,
        })

        # let's make this safe to work with
        code = code.replace('```py\n', '').replace('```', '').replace('`', '')

        _code = 'async def func(self):\n  try:\n{}\n  finally:\n    self._eval[\'env\'].update(locals())'\
            .format(textwrap.indent(code, '    '))

        before = time.monotonic()
        # noinspection PyBroadException
        try:
            exec(_code, self._eval['env'])
            func = self._eval['env']['func']
            output = await func(self)

            if output is not None:
                output = repr(output)
        except Exception as e:
            output = '{}: {}'.format(type(e).__name__, e)
        after = time.monotonic()
        self._eval['count'] += 1
        count = self._eval['count']

        code = code.split('\n')
        if len(code) == 1:
            _in = 'In [{}]: {}'.format(count, code[0])
        else:
            _first_line = code[0]
            _rest = code[1:]
            _rest = '\n'.join(_rest)
            _countlen = len(str(count)) + 2
            _rest = textwrap.indent(_rest, '...: ')
            _rest = textwrap.indent(_rest, ' ' * _countlen)
            _in = 'In [{}]: {}\n{}'.format(count, _first_line, _rest)

        message = '```py\n{}'.format(_in)
        if output is not None:
            message += '\nOut[{}]: {}'.format(count, output)
        ms = int(round((after - before) * 1000))
        if ms > 100:  # noticeable delay
            message += '\n# {} ms\n```'.format(ms)
        else:
            message += '\n```'

        try:
            if ctx.author.id == self.bot.user.id:
                await ctx.message.edit(content=message)
            else:
                if not silent:
                    await ctx.send(message)
        except discord.HTTPException:
            if not silent:
                with aiohttp.ClientSession() as sesh:
                    async with sesh.post("https://hastebin.com/documents/", data=output, headers={"Content-Type": "text/plain"}) as r:
                        r = await r.json()
                        embed = discord.Embed(
                            description="[View output - click](https://hastebin.com/raw/{})".format(r["key"]),
                            color=randomness.random_colour()
                        )
                        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Admin(bot))