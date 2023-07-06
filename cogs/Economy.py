import discord
from discord.ext import commands

from modules.user_sqlite import user
from bot_config import bot_config as bcfg
from modules.exceptions import RateError

import time

class Economy(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name='daily', aliases=['day'])
    async def daily(self, ctx: commands.Context) -> None:
        """claim daily reward"""

        author = ctx.author

        footer = bcfg['footer']
        dailymoney = bcfg['dailymoney']

        if user.read(author.id,"daily") + 86400 > time.time():
            raise RateError(msg='You have already claimed your daily reward. Please wait `{0}` to claim it again.'.format(time.strftime('%H hr %M min %S sec', time.gmtime((user.read(author.id,'daily')+86400)-time.time()))))
        else:
            user.add(author.id,"money",dailymoney)
            await ctx.send(embed=discord.Embed(
                    title="Daily Reward",
                    description="You have claimed your daily reward! You got {0} money.".format(dailymoney),
                    color=discord.Color.green(),
                ).set_footer(text=footer)
            )
            user.write(author.id,"daily",time.time())

    @commands.hybrid_command(name='level', aliases=['rank'])
    async def level(self, ctx: commands.Context, usr:discord.Member=None) -> None:
        """check your level"""

        author = ctx.author

        footer = bcfg['footer']
        expincrement = bcfg['expincrement']
        expstart = bcfg['expstart']

        if usr:
            await ctx.send(
                embed=discord.Embed(
                    title="Level",
                    description="<@!{0}>'s level: {1}\nNext level: {2} EXP\nCurrent EXP: {3}".format(usr,user.read(usr.id,"lvl"),(user.read(usr.id,"lvl") * expincrement) + expstart,user.read(usr.id,"exp")),
                    color=discord.Color.red()
                ).set_footer(text=footer)
            )
        else:
            await ctx.send(
                embed=discord.Embed(
                    title="Level",
                    description="Your level: {1}\nNext level: {2} EXP\nCurrent EXP: {3}".format(author.id,user.read(author.id,"lvl"),(user.read(author.id,"lvl") * expincrement) + expstart,user.read(author.id,"exp")),
                    color=discord.Color.red()
                ).set_footer(text=footer)
            )

    @commands.hybrid_command(name='balance', aliases=['bal','bank'])
    async def balance(self, ctx: commands.Context, usr:discord.Member=None) -> None:
        """like a true capitalist"""

        footer = bcfg['footer']

        if not usr:
            if "69" in str(user.read(ctx.author.id,"money")):
                await ctx.send(embed=discord.Embed(
                        title="Bank",
                        description="You currently have {0} money. Nice.".format(user.read(ctx.author.id,"money")),
                        color=discord.Color.orange(),
                    ).set_footer(text=footer)
                )
                return
            await ctx.send(embed=discord.Embed(
                    title="Bank",
                    description="You currently have {0} money.".format(user.read(ctx.author.id,"money")),
                    color=discord.Color.orange(),
                ).set_footer(text=footer)
            )
            return

        if "69" in str(user.read(usr.id,"money")):
            await ctx.send(embed=discord.Embed(
                    title="Bank",
                    description="<@{0}> currently has {1} money. Nice.".format(usr.id,user.read(usr.id,"money")),
                    color=discord.Color.orange(),
                ).set_footer(text=footer)
            )
            return
        await ctx.send(embed=discord.Embed(
                title="Bank",
                description="{0} currently has {1} money.".format("<@{0}>".format(usr.id),user.read(usr.id,"money")),
                color=discord.Color.orange(),
            ).set_footer(text=footer)
        )

    @commands.hybrid_command()
    async def bruh(self, ctx: commands.Context, usr:discord.Member=None) -> None:
        """how many bruhs"""
        bruhs = user.read(ctx.author.id if not usr else usr.id,"bruh")
        await ctx.send("{0} bruhs have been had".format(bruhs))

async def setup(bot) -> None:
    await bot.add_cog(Economy(bot))
    print('Economy loaded')
