from discord import Interaction, Color, ButtonStyle
from discord.ui import Button, View
from discord.ext import commands

from modules.BruhCasinoEmbed import BruhCasinoEmbed
from modules.BruhCasinoGame import BruhCasinoGame
from modules.BruhCasinoCog import BruhCasinoCog

from math import factorial as fc

from random import shuffle

class MinesSpace:
    def __init__(self, is_mine: bool) -> None:
        self.is_mine: bool = is_mine
        self.selected: bool = False

    def select(self) -> bool:
        self.selected = True
        return self.is_mine

class MinesBoard:
    spaces = 24

    @classmethod
    def new(cls, mines: int) -> list[MinesSpace]:
        t: list[MinesSpace] = []
        for i in range(mines):
            t.append(MinesSpace(is_mine=True))
        for i in range(cls.spaces - mines):
            t.append(MinesSpace(is_mine=False))
        for i in range(100):
            shuffle(t)
        return t


class MinesGame(BruhCasinoGame):
    async def _init(self) -> None:
        self.active = True
        self.board: list[MinesSpace] = MinesBoard.new(self.mines)
        for i in self.board:
            print(1 if i.is_mine else 0, end='')
        print()
        self.spaces_cleared: int = 0

        self.buttons = self.get_buttons()

        self.refresh_buttons()
        self.message = await self.send_or_edit(embed=self.get_embed(), view=self.view)

    def __init__(self, cog: BruhCasinoCog, ctx: commands.Context, bet: int, mines: int, *args, **kwargs) -> None:
        super().__init__(cog, ctx, bet, getbuttons=False, *args, **kwargs)

        self.mines: int = mines

    def get_chance(self) -> float:
        real: int = len(self.board) - self.mines
        return (fc(real) * fc(len(self.board) - self.spaces_cleared)) / (fc(len(self.board)) * fc(real - self.spaces_cleared))

    def get_multiplier(self) -> float:
        return round((1 / self.get_chance()), 2)

    def get_winnings(self) -> int:
        return round(self.bet * self.get_multiplier())

    def get_embed(self) -> BruhCasinoEmbed:
        return BruhCasinoEmbed(
            title="Mines",
            description=f"Current Cashout: ${self.bet} x {self.get_multiplier()} = ${self.get_winnings()}",
            color=Color.orange()
        )

    def refresh_buttons(self) -> None:
        for t in range(self.buttons.__len__() - 1):
            b: Button = self.buttons[t]
            m: MinesSpace = self.board[t]
            b.label = '💰' if m.selected else '?'
            b.style = ButtonStyle.green if m.selected else ButtonStyle.grey
            b.disabled = m.selected

        self.buttons[-1].label = f"Cashout ${self.get_winnings()}"

        super().refresh_buttons()

    def get_buttons(self) -> list[Button]:
        t: list[Button] = []
        for i in range(MinesBoard.spaces):
            x: Button = Button(label="?")
            x.callback = lambda ctx, _i=i: self.on_mines_button(ctx, _i)
            t.append(x)
        b: Button = Button(label=f"Cashout ${self.bet}")
        b.callback = self.on_cashout
        t.append(b)
        return t

    def get_retry_button(self) -> View:
        self.view.clear_items()
        for m in self.board:
            self.view.add_item(Button(
                label='💣' if m.is_mine else '💰',
                style=ButtonStyle.red if m.is_mine else (ButtonStyle.green if m.selected else ButtonStyle.grey),
                disabled=True
            ))
        if self.stats.money >= self.bet:
            b: Button = Button(label=f"Play Again (${self.bet})")
            b.callback = self.on_retry
            self.view.add_item(b)

        return self.view

    async def on_timeout(self) -> None:
        if self.active:
            return await super().on_timeout()
        else:
            self.view.clear_items()
            for m in self.board:
                self.view.add_item(Button(
                    label='💣' if m.is_mine else '💰',
                    style=ButtonStyle.red if m.is_mine else (ButtonStyle.green if m.selected else ButtonStyle.grey),
                    disabled=True
                ))
            await self.message.edit(view=self.view)
            del self.message

    async def on_lose(self) -> None:
        self.stats.lost(self.bet)
        self.active = False

        await self.message.edit(embed=BruhCasinoEmbed(
            title="Mines",
            description=f"you lost ${self.bet} lmao",
            color=Color.red()
        ), view=self.get_retry_button())

    async def on_mines_button(self, ctx: Interaction, num: int) -> None:
        await ctx.response.defer()
        if self.board[num].select():
            return await self.on_lose()
        else:
            self.spaces_cleared += 1
            self.refresh_buttons()
            await self.message.edit(embed=self.get_embed(), view=self.view)


    async def on_cashout(self, ctx: Interaction) -> None:
        await ctx.response.defer()
        self.stats.won(self.get_winnings() - self.bet)
        self.active = False

        await self.message.edit(embed=BruhCasinoEmbed(
            title="Mines",
            description=f"You won ${self.get_winnings()}!",
            color=Color.green()
        ), view=self.get_retry_button())
