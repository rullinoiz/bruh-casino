from discord import Interaction, Message
from discord.ext import commands
from discord.ui import Button, View

from modules.exceptions import HandsOffError, CommandTimeoutError
from modules.user_instance import user_instance
from modules.BruhCasinoCog import BruhCasinoCog

from typing import Type
from typing_extensions import Self
from abc import abstractmethod

class BruhCasinoGame(object):

    def __str__(self) -> str:
        return f'<{self.__class__.__name__} {self.__dict__.keys()}>'

    @classmethod
    async def create(cls: Type[Self], cog: BruhCasinoCog, ctx: commands.Context, bet: int) -> Self:
        t: Self = cls(cog, ctx, bet)
        await t._init()
        return t

    @abstractmethod
    async def _init(self) -> None:
        self.message: Message = Message()
        pass

    def __init__(self, cog: BruhCasinoCog, ctx: commands.Context, bet: int, timeout: float = 20) -> None:
        self.ctx: commands.Context = ctx
        self.message: Message
        self.stats = user_instance(ctx)
        self.bet: int = bet
        self.cog: BruhCasinoCog = cog

        self.view: View = View(timeout=timeout)
        self.view.on_timeout = self.on_timeout
        self.view.on_error = cog.bot.on_command_error
        self.view.interaction_check = self.interaction_check

        self.buttons: list[Button] = self.get_buttons()

        self.active: bool = True

    @abstractmethod
    def get_buttons(self) -> list[Button]:
        pass

    def refresh_buttons(self) -> None:
        self.view.clear_items()
        for x in self.buttons: self.view.add_item(x)

    async def interaction_check(self, ctx: Interaction) -> bool:
        if ctx.user == self.ctx.author: return True
        raise HandsOffError()

    async def on_timeout(self) -> None:
        if self.active:
            self.active = False
            e = CommandTimeoutError(time=self.view.timeout, msg=self.message)
            await self.cog.bot.on_command_error(self.ctx, e)
        else:
            await self.message.edit(view=None)
