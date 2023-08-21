import asyncio

import discord
from discord.ext import commands
from discord import app_commands
import typing
import inspect
import os

from modules.user_sqlite import user as userdata
from modules.server import server
from modules.checks import is_developer, is_developer_predicate

from bot_config import bot_config as bcfg

import subprocess as subp

class Debugging(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot: discord.Client = bot

    @commands.hybrid_group(with_app_command=True)
    async def debug(self, ctx: commands.Context) -> None:
        pass

    @debug.command()
    @is_developer()
    async def exit(self, ctx:commands.Context) -> None:
        """kill bot"""
        print("someone invoked {0}".format(ctx.invoked_with))
        await ctx.send("adios")
        await self.bot.close()
    
    @debug.command(name='setmoney')
    @is_developer()
    async def money(self, ctx, user: discord.Member, money: int) -> None:
        """conterfeit money"""
        footer: str = bcfg['footer']

        userdata.write(user,"money",money)
        await ctx.send(embed=discord.Embed(
                title="Success",
                description="Money for user {0} has been successfully set to {1}.".format(str(user.mention),money),
                color=discord.Color.green()
            ).set_footer(text=footer)
        )

    @debug.command(name='reload')
    @is_developer()
    async def reload(self, ctx: commands.Context, cog: str) -> None:
        """reloads a command module"""
        message: discord.Message = ctx.message
        prg: str = f'self.bot.reload_extension(\'{cog}\')'
        
        result = eval(prg)
        if inspect.isawaitable(result):
            result = await result
        ctx.bot.tree.copy_global_to(guild=ctx.guild)
        await ctx.bot.tree.sync(guild=ctx.guild)
        await (message.add_reaction if not ctx.interaction else ctx.send)("✅")

    @reload.autocomplete('cog')
    async def reload_autocomplete(self, ctx: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
        data = []
        for filename in os.listdir('cogs'):
            if filename.endswith('.py'):
                if current.lower() in filename[:-3].lower():
                    data.append(app_commands.Choice(name=filename[:-3],value='cogs.'+filename[:-3]))
        return data

    @debug.command(name='status')
    async def status(self, ctx:commands.Context) -> None:
        ip = subp.run(['ip','addr','show','eth0'], stdout=subp.PIPE, text=True).stdout
        free = subp.run(['free'], stdout=subp.PIPE, text=True).stdout

        await ctx.send(f'result of `ip addr show eth0`:```{ip}```result of `free`:```{free}```')

    @debug.command(name='sql')
    @is_developer('do that shit')
    async def sql(self, ctx: commands.Context, *, prg: str) -> None:
        """we do a little sql injection"""
        try:
            result = userdata.c.execute(str(prg))
            result = result.fetchall()
            if not result:
                userdata.s.commit()
                return await (ctx.message.add_reaction if not ctx.interaction else ctx.send)('✅')
            await ctx.send(result)
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                    title='awkward....',
                    description=f'sql returned an error: ```{type(e).__name__}: {str(e)}```',
                    color=discord.Color.red()
                ).set_footer(text=bcfg['footer'])
            )
    
    @debug.command(name='refresh')
    async def refresh(self, ctx: commands.Context) -> None:
        ctx.bot.tree.copy_global_to(guild=ctx.guild)
        await ctx.bot.tree.sync(guild=ctx.guild)

    @debug.command(name='refreshall')
    @is_developer()
    async def refreshall(self, ctx: commands.Context) -> None:
        await ctx.defer()
        mtoedit: discord.Message = await ctx.send('loading...')
        async for i in self.bot.fetch_guilds():
            ctx.bot.tree.copy_global_to(guild=i)
            await ctx.bot.tree.sync(guild=i)
        await mtoedit.edit(content='done')

    @debug.command(name='changelog',aliases=['git'])
    async def git(self, ctx: commands.Context) -> None:
        proc = await asyncio.create_subprocess_shell(
            'git --no-pager log --pretty=oneline --abbrev-commit --graph --decorate --all',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout,stderr = await proc.communicate()

        stdout = str(stdout)[2:-1].split('\\n')
        stdout = '\n'.join(stdout[:min(15,len(stdout))])

        await ctx.send(embed=discord.Embed(
                title='Changelog',
                description='Changelog for this bot (topmost is latest, last 15 commits shown)\n' + stdout
            ).set_footer(text=bcfg['footer'])
        )

    @debug.command()
    @is_developer()
    async def deletemsg(self, ctx: commands.Context, messages: commands.Greedy[discord.Message]) -> None:
        """delete bot's messages (developer purposes only)"""
        await ctx.defer(ephemeral=True)

        for i in messages:
            await i.delete()

        await ctx.send('done', ephemeral=True)


async def setup(bot) -> None:
    await bot.add_cog(Debugging(bot))
    print('Debugging loaded')
