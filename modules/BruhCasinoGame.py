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
    async def create(cls: Type[Self], cog: BruhCasinoCog, ctx: commands.Context, bet: int, *args, **kwargs) -> Self:
        t: Self = cls(cog, ctx, bet, *args, **kwargs)
        await t._init()
        return t

    @abstractmethod
    async def _init(self) -> None:
        self.message: Message = Message()
        self.active = True
        pass

    def __init__(self, cog: BruhCasinoCog, ctx: commands.Context, bet: int, timeout: float = 20, getbuttons: bool = True) -> None:
        self.ctx: commands.Context = ctx
        self.message: Message
        self.stats = user_instance(ctx)
        self.bet: int = bet
        self.cog: BruhCasinoCog = cog

        self.view: View = View(timeout=timeout)
        self.view.on_timeout = self.on_timeout
        self.view.on_error = cog.bot.on_command_error
        self.view.interaction_check = self.interaction_check

        if getbuttons:
            self.buttons: list[Button] = self.get_buttons()
        else:
            self.buttons = None

        self.active: bool = True

    @abstractmethod
    def get_buttons(self) -> list[Button]:
        pass

    async def on_retry(self, ctx: Interaction) -> None:
        await ctx.response.defer()
        await self._init()

    def get_retry_button(self) -> View:
        self.active = False
        v = None
        if self.stats.money >= self.bet:
            v = self.view
            v.clear_items()
            b = Button(label=f"Play Again (${self.bet})")
            b.callback = self.on_retry
            v.add_item(b)
        return v

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
            del self.message
