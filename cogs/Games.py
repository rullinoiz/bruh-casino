import discord
from discord.ext import commands
from discord.ui import Button,View
import modules.cards as cards
from modules.user_sqlite import user
from modules.user_instance import user_instance
from bot_config import bot_config as bcfg
from modules.videopoker import HandAnalyzer
from modules.BruhCasinoCog import EconomyBruhCasinoCog
from modules.BruhCasinoEmbed import BruhCasinoEmbed
from typing import Callable

import modules.checks as checks
import modules.exceptions as e

import asyncio
from random import randint as random

class Games(EconomyBruhCasinoCog):

    @commands.hybrid_command(name='blackjack',aliases=['bj'])
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    async def blackjack(self, ctx: commands.Context, bet: checks.Money) -> None:
        """blackjack gaming"""
        bet: int = int(bet)
        stats: user_instance = ctx.stats

        footer = bcfg['footer']

        deck: cards.Deck = cards.Deck(decks=2)
        deck.shuffle()

        stats.money -= bet

        dealerhand: cards.BlackjackHand = cards.BlackjackHand(deck=deck.draw(2))
        player: cards.BlackjackHand = cards.BlackjackHand(deck=deck.draw(2))

        if player.is_blackjack() and not dealerhand.is_blackjack():
            await ctx.send(embed=BruhCasinoEmbed(
                    title="Blackjack",
                    description="You have blackjack! You won {0} money.".format(bet*2),
                    color=discord.Color.green()
                ).add_field(
                    name="Dealer ({0})".format(int(dealerhand)),
                    value=str(dealerhand)
                ).add_field(
                    name="You ({0})".format(21),
                    value=str(player)
                )
            )
            stats.add(('money','moneygained','wins'),(bet*3,bet*2,1))
            return
        elif dealerhand.is_blackjack() and not player.is_blackjack():
            await ctx.send(embed=BruhCasinoEmbed(
                    title="Blackjack",
                    description="Dealer has blackjack! You lost {0} money.".format(bet),
                    color=discord.Color.red()
                ).add_field(
                    name="Dealer ({0})".format(21),
                    value=str(dealerhand)
                ).add_field(
                    name="You ({0})".format(player.toVal()),
                    value=str(player)
                )
            )
            stats.add(('moneylost','loss'),(bet,1))
            return
        elif player.is_blackjack() and dealerhand.is_blackjack():
            await ctx.send(embed=BruhCasinoEmbed(
                    title="Blackjack",
                    description="It's a tie! No one wins.",
                    color=discord.Color.red()
                ).add_field(
                    name="Dealer ({0})".format(21),
                    value=str(dealerhand)
                ).add_field(
                    name="You ({0})".format(21),
                    value=str(player)
                )
            )
            stats["money"] += bet
            return
        
        bt: list[Button] = [
            Button(label='Hit'),
            Button(label='Stand'),
            Button(label=f'Double Down (${bet})',disabled=False),
            Button(label=f'Split (${bet})',disabled=player[0].value != player[1].value or stats["money"] < bet)]
        buttons = View(timeout=20)
        for x in bt: buttons.add_item(x)

        mtoedit: discord.Message = await ctx.send(embed=BruhCasinoEmbed(
                title="Blackjack",
                description="Click \"Hit\", \"Stand\", \"Double Down\", or \"Split\" within 20 seconds.",
                color=discord.Color.orange()
            ).add_field(
                name="Dealer (?)",
                value="{0} {1}".format("?",dealerhand[1])
            ).add_field(
                name="You ({0})".format(player.toVal()),
                value=str(player)
            ),
            view=buttons
        )

        player: list[cards.BlackjackHand] = [player]

        def listHands(hands:list[cards.BlackjackHand],current:int=None) -> str:
            val: list[str] = []
            for i,v in enumerate(hands, start=0):
                val.append('{0}{1}{0}'.format('__' if i == current and len(hands) != 1 else ('~~' if v.busted else ''), str(v)))
            return '\n'.join(val)

        for i, playerhand in enumerate(player, start=0):
            stay: bool = False
            bt[2].disabled = stats.read('money') < bet
            bt[3].disabled = playerhand[0].value != playerhand[1].value or stats.read('money') < bet
            while not (stay or playerhand.busted or playerhand.is_blackjack()):
                embed = mtoedit.embeds[0]
                buttons.clear_items()
                for x in bt: buttons.add_item(x)
                await mtoedit.edit(embed=embed.clear_fields()
                    .add_field(
                        name="Dealer (?)",
                        value="{0} {1}".format("?", dealerhand[1])
                    ).add_field(
                        name="You ({0})".format(playerhand.toVal()),
                        value=listHands(player, i)
                    ),
                    view=buttons
                )

                msg = await self.wait_for_button(ctx, mtoedit, bt)
                await msg.response.defer()

                # TODO: Refactor for 3.11 (when it comes out)
                if msg.data['custom_id'] == bt[0].custom_id:  # hit
                    bt[3].disabled = True
                    bt[2].disabled = True
                    playerhand.append(deck.draw())
                
                elif msg.data['custom_id'] == bt[1].custom_id:  # stay
                    stay = True

                elif msg.data['custom_id'] == bt[2].custom_id:  # double
                    stats.subtract('money', bet)
                    playerhand.append(deck.draw())
                    playerhand.doubled = True
                    stay = True

                elif msg.data['custom_id'] == bt[3].custom_id: # split
                    stats.subtract('money', bet)
                    player.insert(i+1, cards.BlackjackHand(playerhand.draw()))
                    playerhand.append(deck.draw())
                    player[i+1].append(deck.draw())
                    bt[3].disabled = playerhand[0].value != playerhand[1].value and stats.read('money')

        embed = mtoedit.embeds[0]

        if player[0].busted and len(player) == 1:
            embed.description = "Bust! You lost {0} money.".format(bet)
            embed.color = discord.Color.red()
            await mtoedit.edit(embed=embed.clear_fields()
                .add_field(
                    name="Dealer ({0})".format(dealerhand.toVal()),
                    value=str(dealerhand)
                ).add_field(
                    name="You ({0})".format(player[0].toVal()),
                    value=listHands(player)
                ),
                view=None
            )
            stats.add(('moneylost', 'loss'), (bet, 1))
            return

        embed.description = 'Waiting for dealer...'
        while not (dealerhand.busted or int(dealerhand) >= 17):
            await mtoedit.edit(embed=embed.clear_fields()
                .add_field(
                    name="Dealer ({0})".format(dealerhand.toVal()),
                    value=str(dealerhand)
                ).add_field(
                    name="You ({0})".format(', '.join([str(x.toVal()) for x in player])),
                    value=listHands(player)
                ),
                view=None
            )
            await asyncio.sleep(1)
            dealerhand.append(deck.draw())

        toSend: list[str] = []
        moneyWon: int = 0
        gameWorth: int = 0
        for d in player:
            if d.busted:
                toSend.append(listHands([d]))
                gameWorth += bet*2 if d.doubled else bet
            elif int(d) > int(dealerhand) or dealerhand.busted:
                toSend.append(f'{"🟩" if len(player) > 1 else ""}{str(d)}')
                gameWorth += bet*2 if d.doubled else bet
                moneyWon += bet*4 if d.doubled or d.is_blackjack() else bet*2
            elif int(d) < int(dealerhand):
                toSend.append(f'{"🟥" if len(player) > 1 else ""}{str(d)}')
                gameWorth += bet*2 if d.doubled else bet
            elif int(d) == int(dealerhand):
                toSend.append(f'{"🟨" if len(player) > 1 else ""}{str(d)}')
                gameWorth += bet*2 if d.doubled else bet
                moneyWon += bet*2 if d.doubled else bet


        if moneyWon < gameWorth:
            embed.description = f'You lost ${gameWorth-moneyWon}!'
            embed.color = discord.Color.red()
            stats.add(('moneylost','loss'),(gameWorth-moneyWon,1))
        elif moneyWon == gameWorth:
            embed.description = f'You broke even with ${moneyWon}!'
            embed.color = discord.Color.yellow()
            stats.add('money',gameWorth)
        elif moneyWon > gameWorth:
            embed.description = f'You won ${moneyWon-gameWorth}!'
            embed.color = discord.Color.green()
            stats.add(('money','moneygained','wins'),(moneyWon,moneyWon-gameWorth,1))

        await mtoedit.edit(embed=embed.clear_fields()
            .add_field(
                name="Dealer ({0})".format(dealerhand.toVal()),
                value=str(dealerhand)
            ).add_field(
                name="You ({0})".format(', '.join([str(x.toVal()) for x in player])),
                value='\n'.join(toSend)
            ),
            view=None
        )

    @commands.hybrid_command(name='war')
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    @checks.under_construction()
    async def war(self, ctx: commands.Context, ante: checks.Money, tie: checks.Money = 0) -> None:
        """tie pays 12:1"""
        footer = bcfg['footer']

        if ante + tie > ctx.stats['money']:
            raise e.BrokeError(ante+tie,ctx.stats['money'])

        deck: cards.Deck = cards.Deck()

        dealers: list[cards.Card] = [deck.draw()]
        users: list[cards.Card] = [deck.draw()]

        bt: list[Button] = [Button(label='Go to War! ($'+str(ante)+')'),Button(label='Surrender')]
        buttons = View(timeout=20)
        for x in bt: buttons.add_item(x) 

        if dealers[0].rank == users[0].rank:
            mtoedit: discord.Message = await ctx.send(embed=discord.Embed(
                    title="War",
                    description="It's a tie!" + (" Your tie paid $" + tie*12 + "!") if tie != 0 else "",
                    color=discord.Color.orange(),
                )
                .add_field(name="Dealer",value=dealers[0])
                .add_field(name="You",value=users[0])
                .set_footer(text=footer),
                view=buttons
            )

            ctx.stats.add(('money','moneygained','wins'),(tie*12,tie*12,1))

            try:
                msg = await self.bot.wait_for('interaction', check=lambda i: i.user.id == ctx.author.id and i.type == discord.InteractionType.component and i.data['custom_id'] in [x.custom_id for x in bt], timeout=20.0)
                await msg.response.defer()
            except asyncio.TimeoutError:
                pass

    @commands.hybrid_command(name='russianroulette',aliases=['russian'])
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    async def russianroulette(self, ctx: commands.Context) -> None:
        """only in russia"""

        bot = self.bot

        author = ctx.author

        footer = bcfg['footer']

        gun = "🔫"
        boom = "💥"
        person = list("😐")
        person = person[random(0,len(person)-1)]    
        
        actions = "1. Spin the barrel and shoot\n2. Shoot\n"
        playerthing = "{0}\n\nYour turn\n\n👤 {1}\n\nYou will...\n{2}\nClick an action below."
        
        barrel = [0,0,0,0,0,0]
        pointer = random(0,5)
        
        barrel[random(0,len(barrel)-1)] = 1
                
        print(str(barrel))
        dead = False
        botdead = False
        
        survived = 0
        bullets = 1
        sincespin = 0

        bt: list[Button] = [Button(label='Spin and shoot'),Button(label='Shoot')]
        buttons = View(timeout=20)
        for x in bt: buttons.add_item(x)

        def chances() -> float:
            return int((bullets / (len(barrel)-sincespin))*10000) / 100

        mtoedit = await ctx.send(embed=discord.Embed(
                    title="Russian Roulette",
                    description=playerthing.format(person,gun,actions),
                    color=discord.Color.orange(),
                ).set_footer(text=footer).add_field(name="Shots Survived",value=survived).add_field(name="Chance of freaking dying",value=str(chances()) + "%"),
                view=buttons
        )

        while not dead and not botdead:
            msg = await self.wait_for_button(ctx, mtoedit, bt)
            await msg.response.defer()
            try:
                msg = await bot.wait_for("interaction", check=lambda i: i.user.id == author.id and i.type == discord.InteractionType.component and i.data['custom_id'] in [x.custom_id for x in bt], timeout=20.0)
                await msg.response.defer()
            except asyncio.TimeoutError:
                raise e.CommandTimeoutError(time=20, msg=mtoedit)
            
            # user stuff
            print(pointer)
            if msg.data['custom_id'] == bt[0].custom_id:
                for i in range(0,random(1,10)):
                    pointer = random(0,5)
                sincespin = 1
                print(pointer)
                
                if barrel[pointer] == 1:
                    dead = True
                    user.add(author.id,"loss",1)
                    break
                
                pointer = pointer + 1
                if pointer >= 6:
                    pointer = 0
            elif msg.data['custom_id'] == bt[1].custom_id:
                sincespin += 1
                print(pointer)
                if barrel[pointer] == 1:
                    dead = True
                    user.add(author.id,"loss",1)
                    break
                else:
                    pointer = pointer + 1
                    if pointer >= 6:
                        pointer = 0
                    
            # bot stuff (super complex algorithm!!)!
            
            survived += 1
            await mtoedit.edit(embed=discord.Embed(
                    title="Russian Roulette",
                    description="{0}{1}\nBot's turn\n👤\n\nWaiting for response...\n".format(person,gun,actions),
                    color=discord.Color.orange(),
                ).set_footer(text=footer).add_field(name="Shots Survived",value=survived,inline=False).add_field(name="Chance of freaking dying",value=str(chances()) + "%",inline=False),
                view=None
            )
            
            await asyncio.sleep(2)
            if chances() < 50:
                print(pointer)
                sincespin += 1
                if barrel[pointer] == 1:
                    botdead = True
                    user.add(author.id,"wins",1)
                    break
                else:
                    pointer = pointer + 1
                    if pointer >= 6:
                        pointer = 0
            else:
                for i in range(0,random(1,10)):
                    pointer = random(0,5)
                sincespin = 1
                print(pointer)
                
                if barrel[pointer] == 1:
                    botdead = True
                    break
                
                pointer = pointer + 1
                if pointer >= 6:
                    pointer = 0

            await mtoedit.edit(embed=discord.Embed(
                    title="Russian Roulette",
                    description=playerthing.format(person,gun,actions),
                    color=discord.Color.orange(),
                ).set_footer(text=footer).add_field(name="Shots Survived",value=survived).add_field(name="Chance of freaking dying",value=str(chances()) + "%"),
                view=buttons
            )
            
        if dead:
            await mtoedit.edit(embed=discord.Embed(
                    title="Russian Roulette",
                    description="🙂🕶👌\noof\n👤{0}{1}\n\nYou ate lead!\n".format(boom,gun),
                    color=discord.Color.red(),
                ).set_footer(text=footer).add_field(name="Shots Survived",value=survived).add_field(name="Chance of freaking dying",value=str(chances()) + "%"),
                view=None
            )
            await asyncio.sleep(0.5)
            await mtoedit.edit(embed=discord.Embed(
                    title="Russian Roulette",
                    description="😎👌\noof\n👤{1}{2}\n\nYou ate lead!\n".format(person,boom,gun),
                    color=discord.Color.red(),
                ).set_footer(text=footer).add_field(name="Shots Survived",value=survived).add_field(name="Chance of freaking dying",value=str(chances()) + "%")
            )
            return
        elif botdead:
            await mtoedit.edit(embed=discord.Embed(
                    title="Russian Roulette",
                    description="😵{0}{1}\noof\n👤\n\nThe bot ate lead!\n".format(boom,gun),
                    color=discord.Color.green(),
                ).set_footer(text=footer).add_field(name="Shots Survived",value=survived).add_field(name="Chance of freaking dying",value=str(chances()) + "%"),
                view=None
            )
            return      

    @commands.hybrid_command(name='flip')
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    async def flip(self, ctx: commands.Context, bet: checks.Money) -> None:
        """flip coin for moneyz"""
        author = ctx.author

        footer = bcfg['footer']

        x = random(0,1)
        bt = [Button(label='Heads'),Button(label='Tails')]
        buttons = View(timeout=10).add_item(bt[0]).add_item(bt[1])

        mtoedit = await ctx.send(embed=BruhCasinoEmbed(
                title="Coin Flip",
                description="Respond with \"Heads\" or \"Tails\" in 10 seconds",
                color=discord.Color.orange()
            ),
            view=buttons
        )

        msg = await self.wait_for_button(ctx=ctx, mtoedit=mtoedit, buttons=bt, timeout=10)
        await msg.response.defer()

        if bt[x].custom_id == msg.data['custom_id']:
            await mtoedit.edit(embed=BruhCasinoEmbed(title="Coin Flip",description="You won {0} money!".format(bet),color=discord.Color.green()),view=None)
            user.add(author.id,('moneygained','wins','money'),(bet,1,bet))
            print("won")
        else:
            await mtoedit.edit(embed=BruhCasinoEmbed(title="Coin Flip",description="You lost {0} money!".format(bet),color=discord.Color.red()),view=None)
            user.add(author.id,('moneylost','loss','money'),(bet,1,-bet))
            print("loss")

    @commands.hybrid_command(name='doubleornothing',aliases=['double','db'])
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    @checks.caller_has_money(50)
    async def double(self, ctx: commands.Context) -> None:
        """bet = $50, hit x10 for 800000 money"""
        bet: int = ctx.caller_has_money
        
        chance: int = 65
        jackpot: int = 800000
        multiplier_image: list[str] = [
            'https://cdn.discordapp.com/attachments/1116943999824035882/1121627385125687356/x0.png',
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
        start_image: str = 'https://cdn.discordapp.com/attachments/1116943999824035882/1121621654292934686/start.png'
        jackpot_image: str = ''

        bt: list[Button] = [Button(label='Double'),Button(label='Cash Out',disabled=True)]
        buttons: View = View(timeout=10)
        for x in bt: buttons.add_item(x)

        current_multiplier = 0
        lost = False
        won = False
        
        mtoedit = await ctx.send(embed=BruhCasinoEmbed(
                title="Double or Nothing",
                description='Current Cash Out: $0',
                color=discord.Color.orange()
            ).set_image(url=start_image),
            view=buttons
        )

        while not lost and not won:
            msg = await self.wait_for_button(ctx=ctx, mtoedit=mtoedit, buttons=bt, timeout=10)
            await msg.response.defer()
            
            bt[1].disabled = False
            buttons.clear_items().add_item(bt[0]).add_item(bt[1])
            embed = mtoedit.embeds[0]
            if msg.data['custom_id'] == bt[0].custom_id:
                if random(1,100) <= chance:
                    current_multiplier += 1
                    if current_multiplier >= 10:
                        won = True
                        break

                    embed.description = f'Current Cash Out: ${bet * (2**(current_multiplier-1))}'
                    embed.set_image(url=multiplier_image[current_multiplier])
                    await mtoedit.edit(embed=embed,view=buttons)
                else:
                    lost = True
                    break
            elif msg.data['custom_id'] == bt[1].custom_id:
                if current_multiplier == 0:
                    mon = 0
                else:
                    mon = bet * (2**(current_multiplier-1))
                embed.color = discord.Color.green()
                embed.set_image(url=cashout_image)
                embed.description = f'You cashed out for ${bet * (2**(current_multiplier-1))}!'
                ctx.stats.won(mon)
                await mtoedit.edit(embed=embed,view=None)
                return
        
        if lost:
            embed.color = discord.Color.red()
            embed.set_image(url=multiplier_image[0])
            embed.description = f'You lost ${bet} lmao'
            ctx.stats.lost(bet)
            await mtoedit.edit(embed=embed,view=None)
            return
        elif won:
            embed.color = discord.Color.yellow()
            embed.set_image(url=jackpot_image)
            embed.description = f'You won a jackpot of ${jackpot}!'
            ctx.stats.won(jackpot)
            await mtoedit.edit(embed=embed,view=None)
            return

    @commands.hybrid_command(name='videopoker')
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    async def videopoker(self, ctx: commands.Context, bet: checks.Money) -> None:
        """yahtzee for stoners"""
        stats = ctx.stats

        deck: cards.Deck = cards.Deck(decks=1)
        deck.shuffle()
        deck.shuffle()

        hand: list[cards.Card] = deck.draw(5)
        handrank1 = HandAnalyzer(''.join([i.videopoker_value for i in hand]))
        handrank2: HandAnalyzer

        buttons: list[Button] = ([Button(label=str(i)) for i in hand] +
                                 [Button(label='Deal', style=discord.ButtonStyle.blurple)])

        if handrank1.pay_current_hand(allpays=1, bet=bet) > 0:
            tohold,_ = handrank1.analyze(False, False)
            for i in range(2,len(tohold)+1,2):
                if tohold[i-2:i] != 'XX':
                    buttons[int((i/2)-1)].style = discord.ButtonStyle.green

        view: View = View(timeout=30)
        for i in buttons: view.add_item(i)

        description: str = 'green to keep\n' + ' '.join([str(i) for i in hand]) + \
                           '\n' + handrank1.pay_current_hand(allpays=3, bet=bet)

        embed: discord.Embed = BruhCasinoEmbed(
            title='Video Poker',
            description=description,
            color=discord.Color.orange()
        )

        firstiter: bool = True
        mtoedit: discord.Message = await ctx.send(embed=embed, view=view)

        stats.money -= bet

        while True:
            if not firstiter:
                await mtoedit.edit(view=view)

            firstiter = False

            msg = await self.wait_for_button(ctx=ctx, mtoedit=mtoedit, buttons=buttons, timeout=int(view.timeout))
            await msg.response.defer()

            bt = msg.data['custom_id']

            if bt == buttons[5].custom_id: # deal
                for i in range(0,4):
                    if buttons[i].style == discord.ButtonStyle.secondary:
                        hand[i] = deck.draw()

                handrank2 = HandAnalyzer(''.join([i.videopoker_value for i in hand]))
                break

            for i in buttons:
                if bt == i.custom_id:
                    i.style = discord.ButtonStyle.secondary if i.style == discord.ButtonStyle.green else discord.ButtonStyle.green
                    view.clear_items()
                    for x in buttons: view.add_item(x)

        description = ' '.join([str(i) for i in hand]) + \
                      '\n' + (handrank2.pay_current_hand(allpays=3, bet=bet) or 'you suck')

        embed.description = description
        embed.color = discord.Color.red() if (won := handrank2.pay_current_hand(allpays=1)) == 0 else discord.Color.green()

        if won > 0:
            stats.add(('money','wins','moneygained'),(bet*won,1,won-bet))
        else:
            stats.add(('loss','moneylost'),(1,bet))

        await mtoedit.edit(embed=embed, view=None)

setup: Callable = Games.setup
