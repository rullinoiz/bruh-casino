import asyncio
from typing import Callable

from modules.BruhCasinoGame import BruhCasinoGame
from modules.BruhCasinoEmbed import BruhCasinoEmbed
from modules.cards import Deck, BlackjackHand

from discord.ui import Button
from discord import Interaction, Color

class BlackjackGame(BruhCasinoGame):
    blackjack_payout: int = 2
    win_payout: int = 1
    dealer_stands_at: int = 17
    bust_at: int = 21

    @property
    def current_hand(self) -> BlackjackHand:
        return self.player[self.current]

    async def _init(self) -> None:
        self.active: bool = True
        self.deck: Deck = Deck(decks=2)
        self.deck.shuffle()

        self.stats['money'] -= self.bet

        self.dealer: BlackjackHand = BlackjackHand(deck=self.deck.draw(2))
        self.player: list[BlackjackHand] = [BlackjackHand(deck=self.deck.draw(2))]

        self.current: int = 0
        self.embed: BruhCasinoEmbed = BruhCasinoEmbed(title="Blackjack", description="Click hit, stand, double down, or split within 20 seconds.", color=Color.orange())

        t: Callable = self.ctx.send if not hasattr(self, "message") else self.message.edit

        if self.dealer.is_blackjack() and not self.current_hand.is_blackjack():
            self.message = await t(embed=BruhCasinoEmbed(
                title="Blackjack",
                description=f"Dealer has blackjack! You lost {self.bet} money.",
                color=Color.red()
            ).add_field(
                name="Dealer (21)",
                value=str(self.dealer)
            ).add_field(
                name=f"You ({self.current_hand.toVal()})",
                value=str(self.current_hand)
            ), view=self.get_retry_button())
            self.stats.add(('moneylost', 'loss'), (self.bet, 1))
        elif self.current_hand.is_blackjack() and not self.dealer.is_blackjack():
            self.message = await t(embed=BruhCasinoEmbed(
                title="Blackjack",
                description=f"You have blackjack! You won {self.bet * self.blackjack_payout} money!",
                color=Color.green()
            ).add_field(
                name=f"Dealer ({int(self.dealer)})",
                value=str(self.dealer)
            ).add_field(
                name="You (21)",
                value=str(self.current_hand)
            ), view=self.get_retry_button())
            self.stats.add(('money','moneygained', 'wins'), (self.bet + self.bet * self.blackjack_payout, self.bet * self.blackjack_payout, 1))
        elif self.current_hand.is_blackjack() and self.dealer.is_blackjack():
            self.message = await t(embed=BruhCasinoEmbed(
                title="Blackjack",
                description="It's a tie! No one wins.",
                color=Color.orange()
            ).add_field(
                name="Dealer (21)",
                value=str(self.dealer)
            ).add_field(
                name="You (21)",
                value=str(self.current_hand)
            ), view=self.get_retry_button())
            self.stats["money"] += self.bet
        else:
            self.refresh_embed()
            self.refresh_buttons()
            self.message = await t(embed=self.embed, view=self.view)

    def refresh_embed(self):
        self.embed.clear_fields() \
        .add_field(
            name="Dealer (?)",
            value=f"? {self.dealer[1]}"
        ) \
        .add_field(
            name=f"You ({int(self.current_hand)})",
            value=self.listHands()
        )

    def listHands(self, display: bool = True) -> str:
        hands: list[BlackjackHand] = self.player
        current: int = self.current if display else None
        val: list[str] = []
        for i, v in enumerate(hands, start=0):
            val.append(
                '{0}{1}{0}'.format('__' if i == current and len(hands) != 1 else ('~~' if v.busted else ''), str(v)))
        return '\n'.join(val)

    def get_buttons(self) -> list[Button]:
        b: list[Button] = [
            Button(label="Hit"),
            Button(label="Stand"),
            Button(label=f"Double Down (${self.bet})", disabled=self.current_hand.__len__() > 2),
            Button(label=f"Split (${self.bet})", disabled=self.current_hand.__len__() != 2 or self.current_hand[0].value != self.current_hand[1].value or self.stats["money"] < self.bet)
        ]
        b[0].callback = self.on_hit
        b[1].callback = self.on_stand
        b[2].callback = self.on_double
        b[3].callback = self.on_split
        return b

    def refresh_buttons(self) -> None:
        self.buttons = self.get_buttons()
        super().refresh_buttons()

    async def calculate_hands(self) -> None:
        toSend: list[str] = []
        moneyWon: int = 0
        gameWorth: int = 0
        for d in self.player:
            gameWorth += self.bet * 2 if d.doubled else self.bet
            if d.busted:
                toSend.append(f"~~{str(d)}~~")
            elif int(d) > int(self.dealer) or self.dealer.busted:
                toSend.append(f'{"🟩" if len(self.player) > 1 else ""}{str(d)}')
                moneyWon += self.bet * 4 if d.doubled or d.is_blackjack() else self.bet * 2
            elif int(d) < int(self.dealer):
                toSend.append(f'{"🟥" if len(self.player) > 1 else ""}{str(d)}')
            elif int(d) == int(self.dealer):
                toSend.append(f'{"🟨" if len(self.player) > 1 else ""}{str(d)}')
                moneyWon += self.bet * 2 if d.doubled else self.bet

        if moneyWon < gameWorth:
            self.embed.description = f'You lost ${gameWorth-moneyWon}!'
            self.embed.color = Color.red()
            self.stats.add(('moneylost','loss'),(gameWorth-moneyWon,1))
        elif moneyWon == gameWorth:
            self.embed.description = f'You broke even with ${moneyWon}!'
            self.embed.color = Color.yellow()
            self.stats.add('money',gameWorth)
        elif moneyWon > gameWorth:
            self.embed.description = f'You won ${moneyWon-gameWorth}!'
            self.embed.color = Color.green()
            self.stats.add(('money','moneygained','wins'),(moneyWon,moneyWon-gameWorth,1))

        await self.message.edit(embed=self.embed.clear_fields()
        .add_field(
            name="Dealer ({0})".format(self.dealer.toVal()),
            value=str(self.dealer)
        ).add_field(
            name="You ({0})".format(', '.join([str(x.toVal()) for x in self.player])),
            value='\n'.join(toSend)
        ),
            view=self.get_retry_button()
        )

    async def run_dealer(self) -> None:
        while not self.dealer.busted and self.dealer.__int__() < self.dealer_stands_at:
            self.embed.description = "Waiting for dealer..."
            await self.message.edit(embed=self.embed.clear_fields()
                .add_field(
                    name=f"Dealer ({self.dealer.toVal()})",
                    value=str(self.dealer)
                )
                .add_field(
                    name="You ({0})".format(', '.join([str(x.toVal()) for x in self.player])),
                    value=self.listHands(False)
                ),
                view=None
            )
            await asyncio.sleep(1)
            self.dealer.append(self.deck.draw())

        await self.calculate_hands()

    async def on_busted(self) -> None:
        self.refresh_embed()
        self.embed.description = f"Bust! You lost ${self.bet}."
        await self.message.edit(embed=self.embed, view=self.get_retry_button())

    async def on_hit(self, ctx: Interaction) -> None:
        await ctx.response.defer()
        self.current_hand.append(self.deck.draw())

        if self.current_hand.busted:
            if self.player.__len__() == 1:
                return await self.on_busted()

            if self.player.__len__() == self.current + 1:
                return await self.run_dealer()
            else:
                self.current += 1

        while self.current_hand.is_blackjack(): self.current += 1

        self.refresh_embed()
        self.refresh_buttons()
        await self.message.edit(embed=self.embed, view=self.view)

    async def on_stand(self, ctx: Interaction) -> None:
        await ctx.response.defer()
        if self.player.__len__() == 1:
            return await self.run_dealer()

        if self.player.__len__() == self.current + 1:
            return await self.run_dealer()
        else:
            self.current += 1

        while self.current_hand.is_blackjack(): self.current += 1

        self.refresh_embed()
        self.refresh_buttons()
        await self.message.edit(embed=self.embed, view=self.view)

    async def on_double(self, ctx: Interaction) -> None:
        await ctx.response.defer()
        self.stats["money"] -= self.bet

        self.current_hand.append(self.deck.draw())
        self.current_hand.doubled = True

        if self.current_hand.busted:
            if self.player.__len__() == 1:
                return await self.on_busted()

        if self.player.__len__() == self.current + 1:
            return await self.run_dealer()
        else:
            self.current += 1

        while self.current_hand.is_blackjack(): self.current += 1

        self.refresh_embed()
        self.refresh_buttons()
        await self.message.edit(embed=self.embed, view=self.view)

    async def on_split(self, ctx: Interaction) -> None:
        await ctx.response.defer()
        self.stats["money"] -= self.bet

        self.player.insert(self.current + 1, BlackjackHand(self.current_hand.draw()))
        self.current_hand.append(self.deck.draw())
        self.player[self.current + 1].append(self.deck.draw())

        self.refresh_embed()
        self.refresh_buttons()
        await self.message.edit(embed=self.embed, view=self.view)
