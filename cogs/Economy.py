import discord
from discord.ext import commands

from modules.user_instance import user_instance
from modules.user_sqlite import user as userdata
from modules.BruhCasinoCog import EconomyBruhCasinoCog
from modules.exceptions import RateError
from typing import Optional

import time

class Economy(EconomyBruhCasinoCog):

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.profile_ctx_menu = discord.app_commands.ContextMenu(
            name='View Profile',
            callback=self.profile_ctx_menu_impl
        )
        self.bot.tree.add_command(self.profile_ctx_menu)

    async def profile_ctx_menu_impl(self, ctx: discord.Interaction, user: discord.Member) -> None:
        t = userdata.read(user,('money','lvl','bruh','wins','loss','moneygained','moneylost'))
        (money,level,bruhs,wins,loss,moneygained,moneylost) = t

        description = f'''{user.mention}\'s profile:
        Money: {money}
        Level: {level}
        Bruhs: {bruhs}
        Wins: {wins}
        Losses: {loss}
        Money Won: {moneygained}
        Money Lost: {moneylost}'''

        # noinspection PyUnresolvedReferences
        await ctx.response.send_message(embed=discord.Embed(description=description).set_footer(text=self.bcfg['footer']))

    @commands.hybrid_command(name='daily', aliases=['day'])
    async def daily(self, ctx: commands.Context) -> None:
        """claim daily reward"""
        stats: user_instance = ctx.stats

        footer = self.bcfg['footer']
        dailymoney = self.bcfg['dailymoney']

        if (t := (stats.daily + 86400)) > time.time():
            raise RateError(
                msg=f'You have already claimed your daily reward. You can claim it again <t:{t}:R>.'
            )
        else:
            stats.money += dailymoney
            await ctx.send(embed=discord.Embed(
                    title="Daily Reward",
                    description=f'You have claimed your daily reward! You got {dailymoney} money.',
                    color=discord.Color.green(),
                ).set_footer(text=footer)
            )
            stats['daily'] = time.time()

    @commands.hybrid_command(name='level', aliases=['rank'])
    async def level(self, ctx: commands.Context, user:discord.Member=None) -> None:
        """check your level"""

        footer = self.bcfg['footer']
        expincrement = self.bcfg['expincrement']
        expstart = self.bcfg['expstart']

        level: int = ctx.stats.lvl if not user else userdata.read(user, 'lvl')
        current_exp: int = ctx.stats.exp if not user else userdata.read(user, 'exp')
        description: str = ("Your" if not user else (user.mention + '\'s')) \
            + f' level: {level}\n' \
            + f'Next level: {(level * expincrement) + expstart}\n' \
            + f'Current EXP: {current_exp}'

        await ctx.send(
            embed=discord.Embed(
                title="Level",
                description=description
            ).set_footer(text=footer)
        )

    @commands.hybrid_command(name='balance', aliases=['bal','bank'])
    async def balance(self, ctx: commands.Context, user: Optional[discord.Member]) -> None:
        """like a true capitalist"""

        footer = self.bcfg['footer']

        money: int = int(ctx.stats.money) if not user else userdata.read(user, 'money')
        description: str = f'{getattr(user, "mention", "You")} currently ha{"ve" if not user else "s"} {money} money.' \
            + (' Nice.' if '69' in str(money) else '')

        send = getattr(t := getattr(ctx, 'send', getattr(ctx, 'response', None)), 'send_message', t)

        await send(embed=discord.Embed(
                title="Bank",
                description=description,
                color=discord.Color.orange(),
            ).set_footer(text=footer),
            #ephemeral=getattr(ctx, 'from_ctx_menu', False)
        )

    @commands.hybrid_command()
    async def bruh(self, ctx: commands.Context, user: Optional[discord.Member]) -> None:
        """how many bruhs"""
        bruhs: int = ctx.stats.bruh if not user else userdata.read(user, 'bruh')
        await ctx.send(f'{bruhs} bruhs have been had')

setup = Economy.setup
