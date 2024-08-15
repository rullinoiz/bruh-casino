import discord
from discord import Interaction, app_commands
from discord.ext import commands
from discord.app_commands import Transform
from modules.user.user_instance import user_instance
from modules.user.user_sqlite import user as userdata
from bc_common.BruhCasinoCog import EconomyBruhCasinoCog
from bc_common.BruhCasinoError import BruhCasinoError
from modules.exceptions import RateError, Uhhhhhh
from bc_common.BruhCasinoEmbed import BruhCasinoEmbed
from modules.transformers import Money
from typing import Optional

import time

class SingularityError(BruhCasinoError):
    def __init__(self) -> None:
        super().__init__("I appreciate the donation, but the devil doesn't take tips", codestyle=False)

class Economy(EconomyBruhCasinoCog):

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.profile_ctx_menu = discord.app_commands.ContextMenu(
            name="View Profile",
            callback=self.profile_ctx_menu_impl
        )
        self.bot.tree.add_command(self.profile_ctx_menu)

    async def profile_ctx_menu_impl(self, ctx: Interaction, user: discord.Member) -> None:
        t = userdata.read(user,("money","lvl","bruh","wins","loss","moneygained","moneylost"))
        (money,level,bruhs,wins,loss,moneygained,moneylost) = t

        description = f"""{user.mention}\'s profile:
        Money: {money}
        Level: {level}
        Bruhs: {bruhs}
        Wins: {wins}
        Losses: {loss}
        Money Won: {moneygained}
        Money Lost: {moneylost}"""

        # noinspection PyUnresolvedReferences
        await ctx.response.send_message(embed=BruhCasinoEmbed(description=description))

    @app_commands.command(name="daily")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def daily(self, ctx: Interaction) -> None:
        """claim daily reward"""
        stats: user_instance = ctx.stats

        if (t := (stats.daily + 86400)) > time.time():
            raise RateError(
                msg=f"You have already claimed your daily reward. You can claim it again <t:{int(t)}:R>."
            )
        else:
            stats.money += stats.lvl * 100
            await ctx.response.send_message(embed=BruhCasinoEmbed(
                    title="Daily Reward",
                    description=f"You have claimed your daily reward! You got {stats.lvl * 100} money.",
                    color=discord.Color.green(),
                )
            )
            stats.daily = time.time()

    @app_commands.command(name="level")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def level(self, ctx: Interaction, user: Optional[discord.Member]) -> None:
        """check your level"""

        expincrement = self.bcfg["expincrement"]
        expstart = self.bcfg["expstart"]

        level: int = ctx.stats.lvl if not user else userdata.read(user, "lvl")
        current_exp: int = ctx.stats.exp if not user else userdata.read(user, "exp")
        description: str = ("Your" if not user else (user.mention + "\'s")) \
            + f" level: {level}\n" \
            + f"Next level: {(level * expincrement) + expstart}\n" \
            + f"Current EXP: {current_exp}"

        await ctx.response.send_message(
            embed=BruhCasinoEmbed(
                title="Level",
                description=description
            )
        )

    @app_commands.command(name="balance")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def balance(self, ctx: Interaction, user: Optional[discord.Member]) -> None:
        """like a true capitalist"""

        money: int = int(ctx.stats.money) if not user else userdata.read(user, 'money')
        description: str = f'{getattr(user, "mention", "You")} currently ha{"ve" if not user else "s"} {money} money.' \
            + (" Nice." if "69" in str(money) else "")

        await ctx.response.send_message(embed=BruhCasinoEmbed(
                title="Bank",
                description=description,
                color=discord.Color.orange(),
            ),
        )

    @app_commands.command(name="pay")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def pay(self, ctx: Interaction, user: discord.Member, amount: Transform[int, Money]) -> None:
        if user == ctx.user: raise Uhhhhhh()
        if user == self.bot.user: raise SingularityError()
        amount = int(amount)

        if amount < 0: raise Uhhhhhh()

        ctx.stats.money -= amount
        userdata.add(user, "money", amount)

        await ctx.response.send_message(embed=BruhCasinoEmbed(
            title="Payment Successful",
            description=f"${amount} has been sent to {user.mention}",
            color=discord.Color.green()
        ))

    @app_commands.command()
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def bruh(self, ctx: Interaction, user: Optional[discord.Member]) -> None:
        """how many bruhs"""
        bruhs: int = ctx.stats.bruh if not user else userdata.read(user, "bruh")
        await ctx.response.send_message(f"{bruhs} bruhs have been had")

setup = Economy.setup
