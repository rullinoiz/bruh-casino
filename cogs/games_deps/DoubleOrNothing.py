from discord import Interaction, Color
from discord.ui import Button

from modules.BruhCasinoEmbed import BruhCasinoEmbed
from modules.BruhCasinoGame import BruhCasinoGame

from random import randint as random

class DoubleOrNothingGame(BruhCasinoGame):
    chance: int = 60
    jackpot: int = 800_000
    multiplier_image: list[str] = [
        'https://cdn.discordapp.com/attachments/1116943999824035882/1121621654292934686/start.png',
        'https://cdn.discordapp.com/attachments/1116943999824035882/1121621595434274876/x1.png',
        'https://cdn.discordapp.com/attachments/1116943999824035882/1121621595170013294/x2.png',
        'https://cdn.discordapp.com/attachments/1116943999824035882/1121621594914168862/x3.png',
        'https://cdn.discordapp.com/attachments/1116943999824035882/1121621594666717235/x4.png',
        'https://cdn.discordapp.com/attachments/1116943999824035882/1121621594419232848/x5.png',
        'https://cdn.discordapp.com/attachments/1116943999824035882/1121621594129842286/x6.png',
        'https://cdn.discordapp.com/attachments/1116943999824035882/1121621593769136268/x7.png',
        'https://cdn.discordapp.com/attachments/1116943999824035882/1121621593530040380/x8.png',
        'https://cdn.discordapp.com/attachments/1116943999824035882/1121621593249038425/x9.png'
    ]
    cashout_image: str = 'https://cdn.discordapp.com/attachments/1116943999824035882/1121621654674624654/cashout.png'
    lost_image: str = 'https://cdn.discordapp.com/attachments/1116943999824035882/1121627385125687356/x0.png'
    jackpot_image: str = 'https://cdn.discordapp.com/attachments/1116943999824035882/1121621655274401802/jackpot.png'

    def __str__(self) -> str:
        return f'<DoubleOrNothingGame m={self.multiplier}, a={self.active}>'

    async def _init(self) -> None:
        self.active: bool = True
        self.multiplier: int = 0

        if not hasattr(self, "message"):
            self.refresh_buttons()
            self.message = await self.ctx.send(embed=self.get_embed(), view=self.view)
        else:
            self.buttons[1].disabled = True
            self.refresh_buttons()
            await self.message.edit(embed=self.get_embed(), view=self.view)

    def get_buttons(self) -> list[Button]:
        t: list[Button] = [Button(label="Double"), Button(label="Cash Out", disabled=True)]
        t[0].callback = self.on_double
        t[1].callback = self.on_cashout
        return t

    def get_embed(self) -> BruhCasinoEmbed:
        return BruhCasinoEmbed(
            title="Double or Nothing",
            description=f"Current Cash Out: ${self.get_cashout()}",
            color=Color.orange()
        ).set_image(url=self.multiplier_image[self.multiplier])

    @classmethod
    def roll(cls) -> bool:
        return random(0, 100) <= cls.chance

    def get_cashout(self) -> int:
        if self.multiplier == 0: return 0
        return self.bet * (2 ** (self.multiplier - 1))

    async def on_double(self, ctx: Interaction) -> None:
        await ctx.response.defer()
        self.buttons[1].disabled = False
        self.refresh_buttons()

        if self.roll():
            self.multiplier += 1
            if self.multiplier == 10:
                return await self.on_jackpot(ctx)

            await ctx.message.edit(embed=self.get_embed(), view=self.view)
        else:
            self.active = False
            self.stats.lost(self.bet)
            await ctx.message.edit(embed=BruhCasinoEmbed(
                title="Double or Nothing",
                description=f"you lost ${self.bet} lmao",
                color=Color.red())
                .set_image(url=self.lost_image),
                view=self.get_retry_button()
            )

    async def on_cashout(self, ctx: Interaction) -> None:
        await ctx.response.defer()
        self.active = False
        self.stats.won(self.get_cashout())
        await ctx.message.edit(embed=BruhCasinoEmbed(
            title="Double or Nothing",
            description=f"You cashed out for ${self.get_cashout()}!",
            color=Color.green()
        ).set_image(url=self.cashout_image),
            view=self.get_retry_button()
        )

    async def on_jackpot(self, ctx: Interaction) -> None:
        self.active = False
        self.stats.won(self.jackpot)
        await ctx.message.edit(embed=BruhCasinoEmbed(
            title="Double or Nothing",
            description=f"You won a jackpot of ${self.jackpot}!",
            color=Color.yellow()
        ).set_image(url=self.jackpot_image),
            view=self.get_retry_button()
        )

