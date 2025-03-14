import asyncio

import discord
from discord.ext import commands
from discord import app_commands, Interaction
import typing
import inspect
import os

from modules.exceptions import AccessDenied
from modules.user.user_sqlite import user as userdata
from modules.checks import is_developer, is_developer_slash_command
from bc_common.BruhCasinoCog import BruhCasinoCog

from bot_config import bot_config as bcfg

import subprocess as subp


class Debugging(BruhCasinoCog):

    debug = app_commands.Group(name="debug", description="debugging stuff")

    @debug.command()
    @is_developer_slash_command()
    async def exit(self, ctx: Interaction) -> None:
        """kill bot"""
        await ctx.response.send_message("adios")
        await self.bot.close()
    
    @debug.command(name="setmoney")
    @is_developer_slash_command()
    async def money(self, ctx: Interaction, user: discord.Member, money: int) -> None:
        """conterfeit money"""
        footer: str = bcfg['footer']

        userdata.write(user,"money", money)
        await ctx.response.send_message(embed=discord.Embed(
                title="Success",
                description="Money for user {0} has been successfully set to {1}.".format(str(user.mention),money),
                color=discord.Color.green()
            ).set_footer(text=footer)
        )

    @debug.command(name="reload")
    @is_developer_slash_command()
    async def reload(self, ctx: Interaction, cog: str) -> None:
        """reloads a command module"""
        await ctx.response.defer(ephemeral=True)
        prg: str = f'self.bot.reload_extension(\'{cog}\')'
        
        result = eval(prg)
        if inspect.isawaitable(result): await result
        self.bot.tree.copy_global_to(guild=ctx.guild)
        await self.bot.tree.sync(guild=ctx.guild)
        await ctx.followup.send("done", ephemeral=True)

    @reload.autocomplete("cog")
    async def reload_autocomplete(self, ctx: Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
        self.UNUSED(ctx)
        data = []
        for filename in os.listdir('cogs'):
            if filename.endswith('.py'):
                if current.lower() in filename[:-3].lower():
                    data.append(app_commands.Choice(name=filename[:-3],value='cogs.'+filename[:-3]))
        return data

    @debug.command(name="status")
    @is_developer_slash_command()
    async def status(self, ctx:commands.Context) -> None:
        ip = subp.run(['ip','addr','show','eth0'], stdout=subp.PIPE, text=True).stdout
        free = subp.run(['free'], stdout=subp.PIPE, text=True).stdout

        await ctx.response.send_message(f'result of `ip addr show eth0`:```{ip}```result of `free`:```{free}```')

    @debug.command(name="sql")
    @is_developer_slash_command("do that shit")
    async def sql(self, ctx: Interaction, *, prg: str) -> None:
        """we do a little sql injection"""
        if "drop" in prg.lower(): raise AccessDenied()
        try:
            result = userdata.c.execute(str(prg))
            result = result.fetchall()
            if not result:
                userdata.s.commit()
                await ctx.response.send_message("cool and good", ephemeral=True)
                return
            await ctx.response.send_message(result, ephemeral=True)
        except Exception as e:
            await ctx.response.send_message(embed=discord.Embed(
                    title='awkward....',
                    description=f'sql returned an error: ```{type(e).__name__}: {str(e)}```',
                    color=discord.Color.red()
                ).set_footer(text=bcfg['footer'])
            )
    
    @debug.command(name="refresh")
    @is_developer_slash_command()
    async def refresh(self, ctx: commands.Context) -> None:
        await ctx.response.defer(ephemeral=True)
        self.bot.tree.copy_global_to(guild=ctx.guild)
        await self.bot.tree.sync(guild=ctx.guild)
        await ctx.followup.send("done")

    @debug.command(name="refreshall")
    @is_developer_slash_command()
    async def refreshall(self, ctx: commands.Context) -> None:
        await ctx.response.defer(ephemeral=True)
        async for i in self.bot.fetch_guilds():
            self.bot.tree.copy_global_to(guild=i)
            await self.bot.tree.sync(guild=i)
        await ctx.followup.send(content='done', ephemeral=True)

    @debug.command(name="clearall")
    @is_developer_slash_command()
    async def clearall(self, ctx: commands.Context) -> None:
        await ctx.response.defer(ephemeral=True)
        async for i in self.bot.fetch_guilds():
            self.bot.tree.clear_commands(guild=i)
            await self.bot.tree.sync(guild=i)
        await ctx.followup.send("done", ephemeral=True)

    @debug.command(name="sync")
    @is_developer_slash_command()
    async def sync(self, ctx: commands.Context) -> None:
        await ctx.response.defer(ephemeral=True)
        await self.bot.tree.sync()
        await ctx.followup.send(content='done', ephemeral=True)

    @app_commands.command(name="changelog")
    async def git(self, ctx: Interaction) -> None:
        proc = await asyncio.create_subprocess_shell(
            'git --no-pager log --pretty=oneline --abbrev-commit --graph --decorate --all',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout,stderr = await proc.communicate()

        stdout = str(stdout)[2:-1].split('\\n')
        stdout = '\n'.join(stdout[:min(15,len(stdout))])

        await ctx.response.send_message(embed=discord.Embed(
                title='Changelog',
                description='Changelog for this bot (topmost is latest, last 15 commits shown)\n' + stdout
            ).set_footer(text=bcfg['footer'])
        )

    @debug.command()
    @is_developer_slash_command()
    async def deletemsg(self, ctx: Interaction, message: int) -> None:
        """delete bot's messages (developer purposes only)"""
        await ctx.response.defer(ephemeral=True)

        message = await ctx.fetch_message(message)
        await message.delete()
        await ctx.followup.send('done', ephemeral=True)

setup = Debugging.setup
