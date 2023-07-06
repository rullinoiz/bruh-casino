import discord
from discord.ext import commands
from discord import app_commands
import typing
import inspect
import os

from modules.user_sqlite import user as user_
from modules.server import server
from modules.checks import is_developer

from bot_config import bot_config as bcfg

import subprocess as subp

class Debugging(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command()
    @is_developer()
    async def exit(self, ctx:commands.Context) -> None:
        """kill bot"""
        print("someone invoked {0}".format(ctx.invoked_with))
        await ctx.send("adios")
        await self.bot.close()
    
    @commands.hybrid_command(name='setmoney')
    @is_developer()
    async def money(self, ctx, user:discord.Member, money:int) -> None:
        """conterfeit money"""
        footer = bcfg['footer']

        user_.write(str(user.id),"money",money)
        await ctx.send(embed=discord.Embed(
                title="Success",
                description="Money for user <@{0}> has been successfully set to {1}.".format(str(user.id),money),
                color=discord.Color.green()
            ).set_footer(text=footer)
        )

    @commands.hybrid_command(name='reload')
    @is_developer()
    async def reload(self, ctx:commands.Context, cog:str) -> None:
        """reloads a command module"""
        message = ctx.message
        prg = f'self.bot.reload_extension(\'{cog}\')'
        
        result = eval(prg)
        if inspect.isawaitable(result):
            result = await result
        await (message.add_reaction if not ctx.interaction else ctx.send)("✅")
        ctx.bot.tree.copy_global_to(guild=ctx.guild)
        await ctx.bot.tree.sync(guild=ctx.guild)
        return

    @reload.autocomplete('cog')
    async def reload_autocomplete(self, ctx:discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
        data = []
        for filename in os.listdir('cogs'):
            if filename.endswith('.py'):
                if current.lower() in filename[:-3].lower():
                    data.append(app_commands.Choice(name=filename[:-3],value='cogs.'+filename[:-3]))
        return data
    # @commands.command()
    # async def args(self, ctx, arg=None) -> None:
    #     await ctx.send(type(arg).__name__)

    @commands.hybrid_command(name='status')
    async def status(self, ctx:commands.Context) -> None:
        ip = subp.run(['ip','addr','show','eth0'], stdout=subp.PIPE, text=True).stdout
        free = subp.run(['free'], stdout=subp.PIPE, text=True).stdout

        await ctx.send(f'result of `ip addr show eth0`:```{ip}```result of `free`:```{free}```')

    @commands.hybrid_command(name='sql')
    @is_developer('do that shit')
    async def sql(self, ctx:commands.Context, *, prg:str) -> None:
        """we do a little sql injection"""

        print(f'{prg} {type(prg)}')
        try:
            result = user_.c.execute(str(prg))
            result = result.fetchall()
            if not result:
                user_.s.commit()
                return await (ctx.message.add_reaction if not ctx.interaction else ctx.send)('✅')
            await ctx.send(result)
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                    title='awkward....',
                    description=f'sql returned an error: ```{type(e).__name__}: {str(e)}```',
                    color=discord.Color.red()
                ).set_footer(text=bcfg['footer'])
            )
    
    @commands.hybrid_command(name='refresh')
    async def refresh(self, ctx: commands.Context) -> None:
        ctx.bot.tree.copy_global_to(guild=ctx.guild)
        await ctx.bot.tree.sync(guild=ctx.guild)

async def setup(bot) -> None:
    await bot.add_cog(Debugging(bot))
