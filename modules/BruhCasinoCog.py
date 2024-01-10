import asyncio

import discord
from typing import Awaitable, TypeVar
from discord.ext import commands

from modules.user_instance import user_instance
from modules.exceptions import CommandTimeoutError
from bot_config import bot_config as bcfg

_T = TypeVar('_T')

class BruhCasinoCog(commands.Cog):
    bcfg: dict = bcfg

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @classmethod
    async def setup(cls, bot) -> None:
        await bot.add_cog(cls(bot))
        print(f'{cls.__name__} loaded')

    @staticmethod
    def send_or_react(ctx: commands.Context, message: str) -> Awaitable:
        if ctx.interaction:
            return ctx.send(message)
        else:
            return ctx.message.add_reaction(message)

    @staticmethod
    def UNUSED(x: _T) -> _T: return x

    async def wait_for_button(self, ctx: commands.Context, mtoedit: discord.Message, buttons: list[discord.Button], timeout: int = 20) -> discord.Interaction[discord.Client]:
        try:
            return await self.bot.wait_for("interaction", check=lambda i: i.user.id == ctx.author.id and i.type == discord.InteractionType.component and i.data['custom_id'] in [x.custom_id for x in buttons], timeout=timeout)
        except asyncio.TimeoutError:
            raise CommandTimeoutError(time=timeout, msg=mtoedit)

class EconomyBruhCasinoCog(BruhCasinoCog):
    async def cog_before_invoke(self, ctx:commands.Context) -> None:
        ctx.stats = user_instance(ctx)
