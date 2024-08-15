from discord import Interaction, Message, Member
from discord.ui import Button, View
import time

from modules.exceptions import HandsOffError, CommandTimeoutError
from modules.user.user_instance import user_instance
from bc_common.BruhCasinoCog import BruhCasinoCog

from typing import Type, Optional
from typing_extensions import Self
from abc import abstractmethod


# noinspection PyUnresolvedReferences
class BruhCasinoGame(object):

    def __str__(self) -> str:
        return f'<{self.__class__.__name__} {self.__dict__.keys()}>'

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, value: bool) -> None:
        self._active = value
        if not value:
            self.lastactive = time.time()


    @classmethod
    async def create(cls: Type[Self], cog: BruhCasinoCog, ctx: Interaction, bet: int, *args, **kwargs) -> Self:
        t: Self = cls(cog, ctx, bet, *args, **kwargs)
        await t._init(ctx)
        return t

    @abstractmethod
    async def _init(self, ctx: Interaction) -> None:
        self.message = Message()
        self.active = True
        pass

    def __init__(self, cog: BruhCasinoCog, ctx: Interaction, bet: int, timeout: float = 20, getbuttons: bool = True) -> None:
        self.ctx: Interaction = ctx
        self.message: Optional[Message] = None
        self.stats = user_instance(ctx)
        self.bet: int = bet
        self.cog: BruhCasinoCog = cog
        self.owner: Member = ctx.user
        self.lastactive: float = time.time()

        self.view: View = View(timeout=timeout)
        self.view.on_timeout = self.on_timeout
        self.view.on_error = cog.bot.command_error
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
        await self._init(ctx)

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

    async def update_message(self, ctx: Optional[Interaction] = None, *args, **kwargs) -> None:
        ctx = ctx or self.ctx
        if ctx.response.is_done():
            await ctx.edit_original_response(*args, **kwargs)
        else:
            await ctx.response.edit_message(*args, **kwargs)

    async def interaction_check(self, ctx: Interaction) -> bool:
        if ctx.user == self.owner: return True
        raise HandsOffError()

    async def on_timeout(self) -> None:
        if self.active:
            self.active = False
            raise CommandTimeoutError(time=self.view.timeout, msg=self.message)
        else:
            print("deleting message", self.message is None)
            await self.message.edit(view=None)
            del self.message

    async def send_or_edit(self, *args, **kwargs) -> None:
        if self.message:
            await self.update_message(self.ctx, *args, **kwargs)
        else:
            await self.ctx.response.send_message(*args, **kwargs)
            self.message = await self.ctx.original_response()
