from discord import Interaction, ButtonStyle, Color, Message
from discord.ext import commands
from discord.ui import Button, View

from modules.BruhCasinoCog import BruhCasinoCog
from modules.BruhCasinoGame import BruhCasinoGame
from modules.BruhCasinoEmbed import BruhCasinoEmbed

from random import shuffle, randint
from asyncio import sleep

class SecretLairSpace:
    DANGER = 0
    MONEY = 1
    TORCH = 2

    money_icons: list[str] = ['💎', '💰', '💸']
    danger_icons: list[str] = ['💀']

    def __init__(self, _type: int) -> None:
        self.type: int = _type
        self.selected: bool = False
        if self.type == SecretLairSpace.MONEY:
            self.icon: str = self.money_icons[randint(0, len(self.money_icons) - 1)]
        elif self.type == SecretLairSpace.DANGER:
            self.icon: str = self.danger_icons[randint(0, len(self.danger_icons) - 1)]
        else:
            self.icon: str = '🔦'

    def __str__(self) -> str:
        return self.icon

    def __repr__(self) -> str:
        return str(self.type)

    def select(self) -> int:
        self.selected = True
        return self.type

class SecretLairRow:
    num_columns: int = 4

    def __init__(self, danger: int) -> None:
        self.columns: list[SecretLairSpace] = []
        self.selected: bool = False
        self.revealed: bool = False

        for i in range(danger):
            self.columns.append(SecretLairSpace(SecretLairSpace.DANGER))
        for i in range(self.num_columns - danger):
            self.columns.append(SecretLairSpace(SecretLairSpace.MONEY))

        for i in range(100):
            shuffle(self.columns)

    def __getitem__(self, i: int) -> SecretLairSpace:
        return self.columns[i]

    def select(self, num: int) -> int:
        self.selected = True
        return self.columns[num].select()

    def set_random_money_to_torch(self) -> None:
        t: int = randint(0, self.num_columns - 1)
        while self.columns[t].type != SecretLairSpace.MONEY:
            t = randint(0, self.num_columns - 1)
        self.columns[t] = SecretLairSpace(SecretLairSpace.TORCH)

class SecretLairBoard:
    rows: int = 5

    @classmethod
    def new(cls, danger: int) -> list[SecretLairRow]:
        t: list[SecretLairRow] = []
        for i in range(cls.rows):
            r: SecretLairRow = SecretLairRow(danger)
            r.set_random_money_to_torch()
            t.append(r)
            print(r.columns)
        #t[-1].set_random_money_to_torch()
        return t

class SecretLairGame(BruhCasinoGame):

    def __init__(self, cog: BruhCasinoCog, ctx: commands.Context, bet: int, danger: int, *args, **kwargs) -> None:
        super().__init__(cog, ctx, bet, getbuttons=False, *args, **kwargs)

        self.danger: int = danger

    async def _init(self) -> None:
        self.active: bool = True
        self.rows_cleared: int = 0
        self.current_row: int = 0
        self.torches: int = getattr(self, "torches", 0)
        self.board: list[SecretLairRow] = SecretLairBoard.new(self.danger)

        self.buttons: list[Button] = self.get_buttons()

        self.refresh_buttons()
        self.message: Message = await self.send_or_edit(embed=self.get_embed(), view=self.view)

    def get_embed(self) -> BruhCasinoEmbed:
        return BruhCasinoEmbed(
            title="Secret Lair",
            description="You delve deeper into the secret lair...",
            color=Color.orange()
        ).add_field(name="Multiplier", value=self.get_multiplier())

    def get_buttons(self) -> list[Button]:
        t: list[Button] = []
        for i in range(SecretLairBoard.rows):
            for x in range(SecretLairRow.num_columns):
                b: Button = Button(label="?", row=i, style=ButtonStyle.gray, disabled=True)
                b.callback = lambda ctx, c=x: self.on_button_click(ctx, c)
                t.append(b)

        for i in range(SecretLairRow.num_columns):
            t[-(i + 1)].disabled = False
            t[-(i + 1)].style = ButtonStyle.blurple

        t.append(Button(label=f"Cashout ${self.bet}", row=0))
        t[-1].callback = self.on_cashout
        t.append(Button(label=f"Torch (x{self.torches})", row=1, disabled=self.torches == 0))
        t[-1].callback = self.on_use_torch

        return t

    def get_row(self) -> int:
        return SecretLairBoard.rows - (self.current_row % SecretLairBoard.rows) - 1

    def update_buttons(self, show_all: bool = False, end_game: bool = False) -> None:
        for y in range(SecretLairBoard.rows):
            r: SecretLairRow = self.board[y]
            for x in range(SecretLairRow.num_columns):
                s: SecretLairSpace = r[x]
                b: Button = self.buttons[y * SecretLairRow.num_columns + x]
                b.style = ButtonStyle.grey
                if self.get_row() == b.row:
                    b.style = ButtonStyle.blurple
                    b.label = str(s) if r.revealed else '?'
                if self.get_row() < y or show_all:
                    if s.selected or show_all:
                        b.label = str(s)
                        if s.selected and s.type != 0:
                            b.style = ButtonStyle.green
                        else:
                            b.style = ButtonStyle.danger if s.type == 0 else ButtonStyle.grey
                    elif not r.revealed:
                        b.label = '?'
                elif not r.revealed:
                    b.label = '?'
                b.disabled = self.get_row() != b.row or show_all

        if not end_game:
            self.buttons[-2].label = f"Cashout ${self.get_cashout()}"
            self.buttons[-1].disabled = self.torches == 0
            self.buttons[-1].label = f"Torch (x{self.torches})"
        else:
            del self.buttons[-2]
            self.buttons[-1].disabled = True

    def get_retry_button(self) -> View:
        v = self.view
        if self.stats["money"] >= self.bet:
            b: Button = Button(label=f"Play Again (${self.bet})", row=0)
            b.callback = self.on_retry
            v.add_item(b)
        return v

    def get_multiplier(self) -> float:
        return round(1 / (((SecretLairRow.num_columns - self.danger) / SecretLairRow.num_columns) ** self.rows_cleared), 2)

    def get_cashout(self) -> int:
        return round(self.get_multiplier() * self.bet)

    async def on_button_click(self, ctx: Interaction, column: int) -> None:
        await ctx.response.defer()
        row: int = (self.current_row % SecretLairBoard.rows)
        space: SecretLairSpace = self.board[self.get_row()][column]

        if not space.select():
            return await self.on_lose()
        elif space.type == SecretLairSpace.MONEY:
            self.rows_cleared += 1

        e: BruhCasinoEmbed = self.get_embed()

        if space.type == SecretLairSpace.TORCH:
            e.description = "You found a torch! Use it to reveal the current row's traps."
            self.torches += 1

        if self.current_row >= SecretLairBoard.rows - 1 and (self.current_row + 1) % SecretLairBoard.rows == 0:
            e.description += "\nProgressing in 5 seconds..."
            self.update_buttons(show_all=True)
            self.buttons[-1].disabled = True
            self.buttons[-2].disabled = True
            self.refresh_buttons()

            await self.message.edit(embed=e, view=self.view)
            await sleep(5)
            self.board = SecretLairBoard.new(self.danger)
            e = self.get_embed()


        self.current_row += 1

        self.update_buttons()
        self.buttons[-1].disabled = self.torches == 0
        self.buttons[-2].disabled = False
        self.refresh_buttons()

        await self.message.edit(embed=e, view=self.view)

    async def on_lose(self) -> None:
        self.active = False
        self.stats.lost(self.bet)
        self.update_buttons(show_all=True, end_game=True)
        self.refresh_buttons()
        await self.message.edit(embed=BruhCasinoEmbed(
            title="Secret Lair",
            description=f"you lost ${self.bet} lmao",
            color=Color.red()
        ), view=self.get_retry_button())

    async def on_cashout(self, ctx: Interaction) -> None:
        await ctx.response.defer()

        self.active = False
        self.stats.won(self.get_cashout() - self.bet)

        self.update_buttons(show_all=True, end_game=True)
        self.refresh_buttons()
        await self.message.edit(embed=BruhCasinoEmbed(
            title="Secret Lair",
            description=f"You won ${self.get_cashout()}!",
            color=Color.green()
        ), view=self.get_retry_button())

    async def on_use_torch(self, ctx: Interaction) -> None:
        await ctx.response.defer()
        e: BruhCasinoEmbed = self.get_embed()

        if self.board[self.get_row()].revealed:
            e.description = "Your torch is already lit lol"
        else:
            self.board[self.get_row()].revealed = True
            self.torches -= 1
            e.description = "You lit the torch and you can see more clearly."

        self.update_buttons()
        self.refresh_buttons()
        await self.message.edit(embed=e, view=self.view)

    async def on_timeout(self) -> None:
        if self.active:
            return await super().on_timeout()
        else:
            del self.buttons[-1]
            self.refresh_buttons()
            await self.message.edit(view=self.view)
            del self.message
