import discord
from discord.ext import commands
from discord.ui import Button,View
import modules.cards as cards
from modules.user_sqlite import user, user_instance
from bot_config import bot_config as bcfg

import modules.checks as checks
import modules.exceptions as e
import typing

import asyncio
from random import randint as random

class Games(commands.Cog):
    def __init__(self, bot:commands.Bot) -> None:
        self.bot = bot

    async def cog_before_invoke(self, ctx:commands.Context) -> None:
        ctx.stats: user_instance = user_instance(ctx)

    @commands.hybrid_command(name='blackjack',aliases=['bj'])
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    async def blackjack(self, ctx:commands.Context, bet:checks.Money) -> None:
        """blackjack gaming"""
        bot = self.bot

        author: discord.Member = ctx.author
        stats: user_instance = ctx.stats

        footer = bcfg['footer']

        deck: cards.Deck = cards.Deck(decks=2)
        deck.shuffle()
        
        # def cardsToStr(e: list[cards.Card], current:int=0) -> str:
        #     # t = ""
        #     # for i in e:
        #     #     t += i[0] + " "
        #
        #     if type(e) == list[cards.Card]:
        #         return ' '.join([str(i) for i in e])
        #     else:
        #         val = []
        #         for i,v in enumerate(e,start=1):
        #             val.append(' '.join([('__{0}__' if i == current else ('{0}' if aceToInt(cardsToVal(v)) <= 21 else '~~{0}~~')).format(str(x)) for x in v]))
        #
        #         return '\n'.join(val)

        stats.subtract('money', bet)

        dealerhand: cards.BlackjackHand = cards.BlackjackHand(deck=deck.draw(2))
        player: cards.BlackjackHand = cards.BlackjackHand(deck=deck.draw(2))

        if player.is_blackjack() and not dealerhand.is_blackjack():
            await ctx.send(embed=discord.Embed(
                    title="Blackjack",
                    description="You have blackjack! You won {0} money.".format(bet*2),
                    color=discord.Color.green()
                ).add_field(
                    name="Dealer ({0})".format(int(dealerhand)),
                    value=str(dealerhand)
                ).add_field(
                    name="You ({0})".format(21),
                    value=str(player)
                ).set_footer(
                    text=footer
                )
            )
            stats.add(('money','moneygained','wins'),(bet*3,bet*2,1))
            return
        elif dealerhand.is_blackjack() and not player.is_blackjack():
            await ctx.send(embed=discord.Embed(
                    title="Blackjack",
                    description="Dealer has blackjack! You lost {0} money.".format(bet),
                    color=discord.Color.red()
                ).add_field(
                    name="Dealer ({0})".format(21),
                    value=str(dealerhand)
                ).add_field(
                    name="You ({0})".format(player.toVal()),
                    value=str(player)
                ).set_footer(
                    text=footer
                )
            )
            stats.add(('moneylost','loss'),(bet,1))
            return
        elif player.is_blackjack() and dealerhand.is_blackjack():
            await ctx.send(embed=discord.Embed(
                    title="Blackjack",
                    description="It's a tie! No one wins.",
                    color=discord.Color.red()
                ).add_field(
                    name="Dealer ({0})".format(21),
                    value=str(dealerhand)
                ).add_field(
                    name="You ({0})".format(21),
                    value=str(player)
                ).set_footer(
                    text=footer
                )
            )
            stats.add('money', bet)
            return
        
        bt: list[Button] = [Button(label='Hit'),Button(label='Stand'),Button(label=f'Double Down (${bet})',disabled=False),Button(label=f'Split (${bet})',disabled=player[0].value!=player[1].value)]
        buttons = View(timeout=20)
        for x in bt: buttons.add_item(x)

        mtoedit: discord.Message = await ctx.send(embed=discord.Embed(
                title="Blackjack",
                description="Click \"Hit\", \"Stand\", \"Double Down\", or \"Split\" within 20 seconds.",
                color=discord.Color.orange()
            ).add_field(
                name="Dealer (?)",
                value="{0} {1}".format("?",dealerhand[1])
            ).add_field(
                name="You ({0})".format(player.toVal()),
                value=str(player)
            ).set_footer(
                text=footer
            ),
            view=buttons
        )

        player: list[cards.BlackjackHand] = [player]

        def listHands(hands:list[cards.BlackjackHand],current:int=None) -> str:
            val: list[str] = []
            for i,v in enumerate(hands, start=0):
                val.append('{0}{1}{0}'.format('__' if i == current and len(hands) != 1 else ('~~' if v.busted else ''), str(v)))
            return '\n'.join(val)

        for i, playerhand in enumerate(player,start=0):
            stay: bool = False
            bt[2].disabled = stats.read('money') < bet
            bt[3].disabled = playerhand[0].value != playerhand[1].value and stats.read('money') > bet
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

                try:
                    msg = await bot.wait_for("interaction",check=lambda i: i.user.id == author.id and i.type == discord.InteractionType.component and i.data['custom_id'] in [x.custom_id for x in bt], timeout=20.0)
                    await msg.response.defer()
                except asyncio.TimeoutError:
                    raise e.CommandTimeoutError()

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
                continue
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
        elif moneyWon == gameWorth:
            embed.description = f'You broke even with ${moneyWon}!'
            embed.color = discord.Color.yellow()
        elif moneyWon > gameWorth:
            embed.description = f'You won ${moneyWon-gameWorth}!'
            embed.color = discord.Color.green()

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
    async def war(self, ctx:commands.Context, ante:checks.Money, tie:checks.Money=0) -> None:
        """tie pays 12:1"""
        footer = bcfg['footer']

        if ante + tie > user.read(ctx.author.id,'money'):
            raise e.BrokeError(ante+tie,user.read(ctx.author.id,'money'))

        deck = cards.Deck()

        dealers: list[cards.Card] = [deck.draw()]
        users: list[cards.Card] = [deck.draw()]

        bt: list[Button] = [Button(label='Go to War!'),Button(label='Surrender')]
        buttons = View(timeout=20)
        for x in bt: buttons.add_item(x) 

        if dealers.rank == users.rank:
            await ctx.send(embed=discord.Embed(
                    title="War",
                    description="It's a tie!" + (" Your tie paid $" + tie*12 + "!") if tie != 0 else "",
                    color=discord.Color.orange(),
                )
                .add_field(name="Dealer",value=dealers[0])
                .add_field(name="You",value=users[0])
                .set_footer(text=footer),
                view=buttons
            )
            
            user.ensure_existence(ctx.author.id,True)
            user.c.execute(f"""update user set
            money = money + {(tie*10)-ante},
            moneylost = moneylost + {ante},
            moneygained = moneygained + {tie*10},
            wins = wins + 1
            where id = {ctx.author.id}""")
            user.s.commit()

    @commands.hybrid_command(name='russianroulette',aliases=['russian'])
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    async def russianroulette(self, ctx:commands.Context) -> None:
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

        mtoedit = await ctx.send(embed=discord.Embed(
                    title="Russian Roulette",
                    description=playerthing.format(person,gun,actions),
                    color=discord.Color.orange(),
                ).set_footer(text=footer).add_field(name="Shots Survived",value=survived).add_field(name="Chance of freaking dying",value=str(((sincespin + 1) / (6 - bullets))*100) + "%"),
                view=buttons
        )

        while not dead and not botdead:
            try:
                msg = await bot.wait_for("interaction", check=lambda i: i.user.id == author.id and i.type == discord.InteractionType.component and i.data['custom_id'] in [x.custom_id for x in bt], timeout=20.0)
                await msg.response.defer()
            except asyncio.TimeoutError:
                raise e.CommandTimeoutError(20)
            
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
                ).set_footer(text=footer).add_field(name="Shots Survived",value=survived,inline=False).add_field(name="Chance of freaking dying",value=str(((sincespin + 1) / (6 - bullets))*100) + "%",inline=False),
                view=None
            )
            
            await asyncio.sleep(2)
            if ((sincespin + 1) / (6 - bullets))*100 < 80:
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
                ).set_footer(text=footer).add_field(name="Shots Survived",value=survived).add_field(name="Chance of freaking dying",value=str(((sincespin + 1) / (6 - bullets))*100) + "%"),
                view=buttons
            )
            
        if dead:
            await mtoedit.edit(embed=discord.Embed(
                    title="Russian Roulette",
                    description="🙂🕶👌\noof\n👤{0}{1}\n\nYou ate lead!\n".format(boom,gun),
                    color=discord.Color.red(),
                ).set_footer(text=footer).add_field(name="Shots Survived",value=survived).add_field(name="Chance of freaking dying",value=str(((sincespin + 1) / (6 - bullets))*100) + "%"),
                view=None
            )
            await asyncio.sleep(0.5)
            await mtoedit.edit(embed=discord.Embed(
                    title="Russian Roulette",
                    description="😎👌\noof\n👤{1}{2}\n\nYou ate lead!\n".format(person,boom,gun),
                    color=discord.Color.red(),
                ).set_footer(text=footer).add_field(name="Shots Survived",value=survived).add_field(name="Chance of freaking dying",value=str(((sincespin + 1) / (6 - bullets))*100) + "%")
            )
            return
        elif botdead:
            await mtoedit.edit(embed=discord.Embed(
                    title="Russian Roulette",
                    description="😵{0}{1}\noof\n👤\n\nThe bot ate lead!\n".format(boom,gun),
                    color=discord.Color.green(),
                ).set_footer(text=footer).add_field(name="Shots Survived",value=survived).add_field(name="Chance of freaking dying",value=str(((sincespin + 1) / (6 - bullets))*100) + "%"),
                view=None
            )
            return      

    @commands.hybrid_command(name='flip')
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    async def flip(self, ctx:commands.Context, bet:checks.Money) -> None:
        """flip coin for moneyz"""
        author = ctx.author

        footer = bcfg['footer']

        x = random(0,1)
        bt = [Button(label='Heads'),Button(label='Tails')]
        buttons = View(timeout=10).add_item(bt[0]).add_item(bt[1])

        mtoedit = await ctx.send(embed=discord.Embed(
                title="Coin Flip",
                description="Respond with \"Heads\" or \"Tails\" in 10 seconds",
                color=discord.Color.orange()
            ).set_footer(text=footer),
            view=buttons
        )

        try:
            msg = await self.bot.wait_for("interaction",check=lambda i: i.user.id == author.id and i.type == discord.InteractionType.component and i.data['custom_id'] in [b.custom_id for b in bt], timeout=10.0)
            await msg.response.defer()
        except asyncio.TimeoutError:
            raise e.CommandTimeoutError(10)

        if bt[x].custom_id == msg.data['custom_id']:
            await mtoedit.edit(embed=discord.Embed(title="Coin Flip",description="You won {0} money!".format(bet),color=discord.Color.green()).set_footer(text=footer),view=None)
            user.add(author.id,('moneygained','wins','money'),(bet,1,bet))
            print("won")
        else:
            await mtoedit.edit(embed=discord.Embed(title="Coin Flip",description="You lost {0} money!".format(bet),color=discord.Color.red()).set_footer(text=footer),view=None)
            user.add(author.id,('moneylost','loss','money'),(bet,1,-bet))
            print("loss")

    @commands.hybrid_command(name='doubleornothing',aliases=['double','db'])
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    async def double(self, ctx:commands.Context) -> None:
        """bet = $50"""
        bet: int = 50
        if ctx.author.stats.read('money') < bet:
            raise e.BrokeError(50,user.read(ctx.author,'money'))
        
        chance: int = 70
        jackpot: int = 1000000
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
        jackpot_image: str = 'https://cdn.discordapp.com/attachments/1116943999824035882/1121621655274401802/jackpot.png'

        bt: list[Button] = [Button(label='Double'),Button(label='Cash Out',disabled=True)]
        buttons: View = View(timeout=10)
        for x in bt: buttons.add_item(x)

        current_multiplier = 0
        lost = False
        won = False
        
        mtoedit = await ctx.send(embed=discord.Embed(
                title="Double or Nothing",
                description='Current Cash Out: $0',
                color=discord.Color.orange()
            ).set_footer(text=bcfg['footer']).set_image(url=start_image),
            view=buttons
        )

        while not lost and not won:
            try:
                msg = await self.bot.wait_for('interaction',check=lambda i: i.user.id == ctx.author.id and i.type == discord.InteractionType.component and i.data['custom_id'] in [x.custom_id for x in bt], timeout=10)
                await msg.response.defer()
            except asyncio.TimeoutError:
                raise e.CommandTimeoutError(10)
            
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
                user.ensure_existence(ctx.author.id,True)
                user.c.execute("""update user set 
                money = money + ?, 
                moneygained = moneygained + ?,
                wins = wins + 1 
                where id = ?""",(mon,mon,ctx.author.id))
                user.s.commit()
                await mtoedit.edit(embed=embed,view=None)
                return
        
        if lost:
            embed.color = discord.Color.red()
            embed.set_image(url=multiplier_image[0])
            embed.description = f'You lost ${bet} lmao'
            user.ensure_existence(ctx.author.id,True)
            user.c.execute("""update user set
            money = money - ?,
            moneylost = moneylost + ?,
            loss = loss + 1
            where id = ?""",(bet,bet,ctx.author.id))
            user.s.commit()
            await mtoedit.edit(embed=embed,view=None)
            return
        elif won:
            embed.color = discord.Color.yellow()
            embed.set_image(url=jackpot_image)
            embed.description = f'You won a jackpot of ${jackpot}!'
            user.ensure_existence(ctx.author.id,True)
            user.c.execute("""update user set
            money = money + ?,
            moneygained = moneygained + ?,
            wins = wins + 1
            where id = ?""",(jackpot,jackpot,ctx.author.id))
            user.s.commit()
            await mtoedit.edit(embed=embed,view=None)
            return

async def setup(bot) -> None:
    await bot.add_cog(Games(bot))
    print('Games loaded')
