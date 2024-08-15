from discord import ButtonStyle, Interaction
from discord.ui import Button
from modules import cards
from bc_common.BruhCasinoGame import BruhCasinoGame
from modules.videopoker.videopoker import HandAnalyzer


class VideoPoker(BruhCasinoGame):

    async def _init(self) -> None:
        self.active = True
        self.deck: cards.Deck = cards.Deck(decks=1)
        self.hand: list[cards.Card] = self.deck.draw(5)

        self.handrank: HandAnalyzer = HandAnalyzer(''.join([i.videopoker_value for i in self.hand]))



    def get_buttons(self) -> list[Button]:
        b: list[Button] = [Button(label=str(i)) for i in self.hand]
        for i,v in enumerate(b):
            v.callback = lambda ctx: self.select_button(ctx, i)
        b += [Button(label='Deal', style=ButtonStyle.blurple)]
        b[5].callback = self.on_deal
        return b

    async def on_deal(self, ctx: Interaction) -> None:
        pass

    async def select_button(self, ctx: Interaction, index: int) -> None:
        pass
