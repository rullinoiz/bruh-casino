from discord.ext import commands
from discord import app_commands, Interaction, Color, InteractionMessage
from bc_common import BruhCasinoEmbed
from modules.checks import is_developer
from bc_common.BruhCasinoCog import BruhCasinoCog

@app_commands.guild_only()
class Administration(BruhCasinoCog):

    @app_commands.command(name="slowmode")
    @commands.check_any(commands.has_permissions(manage_channels=True), is_developer())
    async def slowmode(self, ctx: Interaction, delay: int) -> None:
        """self explanatory"""
        await ctx.channel.edit(slowmode_delay=delay)
        await ctx.response.send_message("✅")

    @app_commands.command()
    @commands.check_any(commands.has_permissions(manage_channels=True), is_developer())
    async def purge(self, ctx: Interaction, num: int) -> None:
        """delete number of previous messages"""
        await ctx.response.defer(ephemeral=True)
        m: InteractionMessage = await ctx.original_response()

        await ctx.channel.purge(limit=num+1, check=lambda c: c != m)

        await ctx.followup.send(
            embed=BruhCasinoEmbed(
                title="Purge Complete",
                description=f"All {str(num)} message(s) have been purged. Squeaky clean!",
                color=Color.green()
            ), ephemeral=True
        )

setup = Administration.setup
