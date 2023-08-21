import discord
from discord.ext import commands

from modules.user_instance import user_instance
from modules.user_sqlite import user as userdata
from bot_config import bot_config as bcfg
from modules.exceptions import RateError

import time

class Economy(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def cog_before_invoke(self, ctx:commands.Context) -> None:
        ctx.stats = user_instance(ctx)

    @commands.hybrid_command(name='daily', aliases=['day'])
    async def daily(self, ctx: commands.Context) -> None:
        """claim daily reward"""
        stats: user_instance = ctx.stats

        footer = bcfg['footer']
        dailymoney = bcfg['dailymoney']

        if stats.daily + 86400 > time.time():
            raise RateError(
                msg=f'You have already claimed your daily reward. Please wait `{time.strftime("%H hr %M min %S sec", time.gmtime((stats.daily+86400)-time.time()))}` to claim it again.'
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

        footer = bcfg['footer']
        expincrement = bcfg['expincrement']
        expstart = bcfg['expstart']

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
    async def balance(self, ctx: commands.Context, user:discord.Member=None) -> None:
        """like a true capitalist"""

        footer = bcfg['footer']

        money: int = int(ctx.stats.money) if not user else userdata.read(user, 'money')
        description: str = f'{getattr(user, "mention", "You")} currently ha{"ve" if not user else "s"} {money} money.' \
            + (' Nice.' if '69' in str(money) else '')

        await ctx.send(embed=discord.Embed(
                title="Bank",
                description=description,
                color=discord.Color.orange(),
            ).set_footer(text=footer)
        )

    @commands.hybrid_command()
    async def bruh(self, ctx: commands.Context, user:discord.Member=None) -> None:
        """how many bruhs"""
        bruhs: int = ctx.stats.bruh if not user else userdata.read(user, 'bruh')
        await ctx.send(f'{bruhs} bruhs have been had')

async def setup(bot) -> None:
    await bot.add_cog(Economy(bot))
    print('Economy loaded')
