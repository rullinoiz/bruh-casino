import discord
import time
from discord import Interaction, app_commands, User
from discord.ext import commands
from discord.app_commands import Transform
from modules.user import user_instance
from modules.user import user as userdata
from bc_common import BruhCasinoCog, BruhCasinoEmbed, BruhCasinoError
from modules.exceptions import RateError, Uhhhhhh
from modules.transformers import Money
from typing import Optional


class SingularityError(BruhCasinoError):
    def __init__(self) -> None:
        super().__init__("I appreciate the donation, but the devil doesn't take tips", codestyle=False)


# noinspection PyUnresolvedReferences
class Economy(BruhCasinoCog):

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.profile_ctx_menu = discord.app_commands.ContextMenu(
            name="View Profile",
            callback=self.profile_ctx_menu_impl
        )
        self.bot.tree.add_command(self.profile_ctx_menu)

    # noinspection PyMethodMayBeStatic
    async def profile_ctx_menu_impl(self, ctx: Interaction, user: User) -> None:
        t = userdata.read(user, ("money", "lvl", "bruh", "wins", "loss", "moneygained", "moneylost"))
        (money, level, bruhs, wins, loss, moneygained, moneylost) = t

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
        stats: user_instance = user_instance(ctx)

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
    async def level(self, ctx: Interaction, user: Optional[User]) -> None:
        """check your level"""
        stats: user_instance = user_instance(ctx)

        expincrement = self.bcfg["expincrement"]
        expstart = self.bcfg["expstart"]

        level: int = stats.lvl if not user else userdata.read(user, "lvl")
        current_exp: int = stats.exp if not user else userdata.read(user, "exp")
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
    async def balance(self, ctx: Interaction, user: Optional[User]) -> None:
        """like a true capitalist"""
        stats: user_instance = user_instance(ctx)

        money: int = int(stats.money) if not user else userdata.read(user, 'money')
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
    async def pay(self, ctx: Interaction, user: User, amount: Transform[int, Money]) -> None:
        stats: user_instance = user_instance(ctx)
        if user == ctx.user: raise Uhhhhhh()
        if user == self.bot.user: raise SingularityError()
        amount = int(amount)

        if amount < 0: raise Uhhhhhh()

        stats.money -= amount
        userdata.add(user, "money", amount)

        await ctx.response.send_message(embed=BruhCasinoEmbed(
            title="Payment Successful",
            description=f"${amount} has been sent to {user.mention}",
            color=discord.Color.green()
        ))

    @app_commands.command()
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def bruh(self, ctx: Interaction, user: Optional[User]) -> None:
        """how many bruhs"""
        stats: user_instance = user_instance(ctx)
        bruhs: int = stats.bruh if not user else userdata.read(user, "bruh")
        await ctx.response.send_message(f"{bruhs} bruhs have been had")


setup = Economy.setup
