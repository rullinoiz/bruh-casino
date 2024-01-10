import discord
from discord.ext import commands

from bot_config import bot_config as bcfg

from modules.checks import is_developer
from modules.BruhCasinoCog import BruhCasinoCog

class Administration(BruhCasinoCog):

    @commands.hybrid_command(name='slowmode', aliases=['sm','slow'])
    @commands.check_any(commands.has_permissions(manage_channels=True), is_developer())
    async def slowmode(self, ctx:commands.Context, delay:int) -> None:
        """self explanatory"""

        # if not channel.permissions_for(author).manage_channels:
        #     await channel.send(embed=discord.Embed(
        #             title="AccessDenied",
        #             description="You do not have sufficient permissions to \"{0}\".".format(command),
        #             color=discord.Color.red()
        #         ).set_footer(text=footer)
        #     )
        #     return
        
        await ctx.channel.edit(slowmode_delay=delay)
        await self.send_or_react(ctx, "✅")

    @commands.command() # does not exit gracefully as app_command
    @commands.check_any(commands.has_permissions(manage_channels=True),is_developer())
    async def purge(self, ctx:commands.Context, num:int) -> None:
        """delete number of previous messages"""
        footer = bcfg['footer']

        async with ctx.typing():
            await ctx.channel.purge(limit=num+1,check=lambda m: m != ctx.message)

        await ctx.send(
            embed=discord.Embed(
                title="Purge Complete",
                description=f"All {str(num)} message(s) have been purged. Squeaky clean!",
                color=discord.Color.green()
            ).set_footer(text=footer),
            delete_after=3.0
        )

setup = Administration.setup
