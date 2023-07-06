import discord
from discord.ext import commands
from discord.ui import Button,View
import modules.cards as cards
from modules.user_sqlite import user
from bot_config import bot_config as bcfg

import modules.checks as checks
import modules.exceptions as e
import typing

import asyncio
from random import randint as random

class Games(commands.Cog):
    def __init__(self, bot:commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name='blackjack',aliases=['bj'])
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    @checks.under_construction()
    async def blackjack(self, ctx:commands.Context, bet:checks.Money) -> None:
        """blackjack gaming"""

        bot = self.bot

        author = ctx.author

        footer = bcfg['footer']

        deck = cards.Deck(decks=2)
        deck.shuffle()

        def cardsToVal(e: list[cards.Card]) -> typing.Union[str, int]:
            t = 0
            t2 = 0
            a = False
            for i in e:
                if i.value.bj_face_value == 11:
                    if not t + 11 > 21:
                        t += 11
                    else:
                        t += 1
                    t2 += 1
                    a = True
                else:
                    t += i.value.bj_face_value
                    t2 += i.value.bj_face_value

            if t > 21:
                t = t2
            elif t == t2:
                pass
            elif a:
                t = "{0}/{1}".format(t,t2)

            return t

        def aceToInt(e) -> int:
            return int(str(e).split("/")[0])
        
        def cardsToStr(e: typing.Union[list[cards.Card], list[list[cards.Card]]], current:int=0) -> str:
            # t = ""
            # for i in e:
            #     t += i[0] + " "
            
            if type(e) == list[cards.Card]:
                return ' '.join([str(i) for i in e])
            else:
                val = []
                for i,v in enumerate(e,start=1):
                    val.append(' '.join([('__{0}__' if i == current else ('{0}' if aceToInt(cardsToVal(v)) <= 21 else '~~{0}~~')).format(str(x)) for x in v]))

                return '\n'.join(val)

        dealerhand = deck.draw(2)
        player = deck.draw(2)

        if aceToInt(cardsToVal(player)) == 21 and not aceToInt(cardsToVal(dealerhand)) == 21:
            await ctx.send(embed=discord.Embed(
                    title="Blackjack",
                    description="You have blackjack! You won {0} money.".format(bet*2),
                    color=discord.Color.green()
                ).add_field(
                    name="Dealer ({0})".format(cardsToVal(dealerhand)),
                    value=cardsToStr(dealerhand)
                ).add_field(
                    name="You ({0})".format(21),
                    value=cardsToStr(player)
                ).set_footer(
                    text=footer
                )
            )
            user.add(author.id,"money",bet*2)
            user.add(author.id,"moneygained",bet*2)
            user.add(author.id,"wins",1)
            return
        elif aceToInt(cardsToVal(dealerhand)) == 21:
            await ctx.send(embed=discord.Embed(
                    title="Blackjack",
                    description="Dealer has blackjack! You lost {0} money.".format(bet),
                    color=discord.Color.red()
                ).add_field(
                    name="Dealer ({0})".format(21),
                    value=cardsToStr(dealerhand)
                ).add_field(
                    name="You ({0})".format(cardsToVal(player)),
                    value=cardsToStr(player)
                ).set_footer(
                    text=footer
                )
            )
            user.subtract(author.id,"money",bet)
            user.add(author.id,"moneylost",bet)
            user.add(author.id,"loss",1)
            return
        elif aceToInt(cardsToVal(player)) == 21 and aceToInt(cardsToVal(dealerhand)) == 21:
            await ctx.send(embed=discord.Embed(
                    title="Blackjack",
                    description="It's a tie! No one wins.",
                    color=discord.Color.red()
                ).add_field(
                    name="Dealer ({0})".format(21),
                    value=cardsToStr(dealerhand)
                ).add_field(
                    name="You ({0})".format(21),
                    value=cardsToStr(player)
                ).set_footer(
                    text=footer
                )
            )
            return
        
        bt: list[Button] = [Button(label='Hit'),Button(label='Stand'),Button(label='Double Down',disabled=False),Button(label='Split',disabled=player[0].value.bj_face_value!=player[1].value.bj_face_value)]
        buttons = View(timeout=20)
        for x in bt: buttons.add_item(x)

        mtoedit = await ctx.send(embed=discord.Embed(
                title="Blackjack",
                description="Click \"Hit\", \"Stand\", \"Double Down\", or \"Split\" within 20 seconds.",
                color=discord.Color.orange()
            ).add_field(
                name="Dealer (?)",
                value="{0} {1}".format("?",dealerhand[1])
            ).add_field(
                name="You ({0})".format(cardsToVal(player)),
                value=cardsToStr(player)
            ).set_footer(
                text=footer
            ),
            view=buttons
        )

        msg = ""
        stay = False

        player = [player]

        for i, playerhand in enumerate(player,start=0):
            while not stay:
                try:
                    msg = await bot.wait_for("interaction",check=lambda i: i.user.id == author.id and i.type == discord.InteractionType.component and i.data['custom_id'] in [x.custom_id for x in bt], timeout=20.0)
                    await msg.response.defer()
                except asyncio.TimeoutError:
                    await mtoedit.edit(embed=discord.Embed(title="TimeoutError",description="Sorry, you failed to respond in under 20 seconds so I gave up",color=discord.Color.red()).set_footer(text=footer),view=None)
                    print("timeouterror: dude failed to respond under the time limit")
                    return

                if msg.data['custom_id'] == bt[0].custom_id:
                    #await msg.delete()
                    playerhand.append(deck.draw())
                    embed = mtoedit.embeds[0]
                    if type(cardsToVal(playerhand)) != str:
                        if cardsToVal(playerhand) > 21:
                            embed.description = "Bust! You lost {0} money.".format(bet)
                            embed.color = discord.Color.red()
                            await mtoedit.edit(embed=embed.clear_fields()
                                .add_field(
                                    name="Dealer ({0})".format(cardsToVal(dealerhand)),
                                    value=cardsToStr(dealerhand)
                                ).add_field(
                                    name="You ({0})".format(cardsToVal(playerhand)),
                                    value=cardsToStr(playerhand)
                                ),
                                view=None,
                            )
                            user.add(author.id,"money",-bet)
                            user.add(author.id,"moneylost",bet)
                            user.add(author.id,"loss",1)
                            return


                    await mtoedit.edit(embed=embed.clear_fields()
                        .add_field(
                            name="Dealer (?)",
                            value="{0} {1}".format("?",dealerhand[1])
                        ).add_field(
                            name="You ({0})".format(cardsToVal(playerhand)),
                            value=cardsToStr(playerhand)
                        ),
                        view=buttons
                    )
                
                elif msg.data['custom_id'] == bt[1].custom_id:
                    #await button_message.delete()
                    stay = True

        embed = mtoedit.embeds[0]
        embed.description = 'Waiting for dealer...'
        while not aceToInt(cardsToVal(dealerhand)) >= 17:
            await mtoedit.edit(embed=embed.clear_fields()
                .add_field(
                    name="Dealer ({0})".format(cardsToVal(dealerhand)),
                    value=cardsToStr(dealerhand)
                ).add_field(
                    name="You ({0})".format(cardsToVal(playerhand)),
                    value=cardsToStr(playerhand)
                ),
                view=None
            )
            await asyncio.sleep(1)
            dealerhand.append(deck.draw())

        if aceToInt(cardsToVal(playerhand)) > aceToInt(cardsToVal(dealerhand)):
            await mtoedit.edit(embed=discord.Embed(
                    title="Blackjack",
                    description="You are closer to 21! You won {0} money.".format(bet),
                    color=discord.Color.green()
                ).add_field(
                    name="Dealer ({0})".format(cardsToVal(dealerhand)),
                    value=cardsToStr(dealerhand)
                ).add_field(
                    name="You ({0})".format(cardsToVal(playerhand)),
                    value=cardsToStr(playerhand)
                ).set_footer(
                    text=footer
                ),
                view=None
            )
            user.add(author.id,"money",bet)
            user.add(author.id,"moneygained",bet)
            user.add(author.id,"wins",1)
            return
        elif aceToInt(cardsToVal(playerhand)) < aceToInt(cardsToVal(dealerhand)) and aceToInt(cardsToVal(dealerhand)) <= 21:
            await mtoedit.edit(embed=discord.Embed(
                    title="Blackjack",
                    description="Dealer is closer to 21! You lost {0} money.".format(bet),
                    color=discord.Color.red()
                ).add_field(
                    name="Dealer ({0})".format(cardsToVal(dealerhand)),
                    value=cardsToStr(dealerhand)
                ).add_field(
                    name="You ({0})".format(cardsToVal(playerhand)),
                    value=cardsToStr(playerhand)
                ).set_footer(
                    text=footer
                ),
                view=None
            )
            user.add(author.id,"money",-bet)
            user.add(author.id,"moneylost",bet)
            user.add(author.id,"loss",1)
            return
        elif aceToInt(cardsToVal(playerhand)) == aceToInt(cardsToVal(dealerhand)):
            await mtoedit.edit(embed=discord.Embed(
                    title="Blackjack",
                    description="It's a tie! No one wins.",
                    color=discord.Color.red()
                ).add_field(
                    name="Dealer ({0})".format(cardsToVal(dealerhand)),
                    value=cardsToStr(dealerhand)
                ).add_field(
                    name="You ({0})".format(cardsToVal(playerhand)),
                    value=cardsToStr(playerhand)
                ).set_footer(
                    text=footer
                ),
                view=None
            )
            return
        elif aceToInt(cardsToVal(dealerhand)) > 21:
            await mtoedit.edit(embed=discord.Embed(
                    title="Blackjack",
                    description="Dealer busts! You won {0} money.".format(bet),
                    color=discord.Color.green()
                ).add_field(
                    name="Dealer ({0})".format(cardsToVal(dealerhand)),
                    value=cardsToStr(dealerhand)
                ).add_field(
                    name="You ({0})".format(cardsToVal(playerhand)),
                    value=cardsToStr(playerhand)
                ).set_footer(
                    text=footer
                ),
                view=None
            )
            user.add(author.id,"money",bet)
            user.add(author.id,"moneygained",bet)
            user.add(author.id,"wins",1)
            return
        else:
            await ctx.send(embed=discord.Embed(
                    title="What‽",
                    description="Ollin's shitty programming must've done something unexpected. Try again.",
                    color=discord.Color.red()
                ).set_footer(text=footer)
            )
            return

    @commands.hybrid_command(name='war')
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    @checks.under_construction()
    async def war(self, ctx:commands.Context, ante:checks.Money, tie:checks.Money=0) -> None:
        """tie pays 12:1"""
        footer = bcfg['footer']

        if ante + tie > user.read(ctx.author.id,'money'):
            raise e.BrokeError(ante+tie,user.read(ctx.author.id,'money'))
        
        if ante % 2 == 1:
            raise e.ArgumentValueError(f'Argument "ante" must be even! (received odd number "{ante}")')

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
                await mtoedit.edit(embed=discord.Embed(
                        title="TimeoutError",
                        description="Sorry, you failed to respond in under 20 seconds so I gave up",
                        color=discord.Color.red()
                    ).set_footer(text=footer),
                    view=None
                )
                return
            
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
            await mtoedit.edit(embed=discord.Embed(title="TimeoutError",description="Sorry, you failed to respond in under 10 seconds so I gave up",color=discord.Color.red()).set_footer(text=footer),view=None)
            print("timeouterror: dude failed to respond under the time limit")
            return

        if bt[x].custom_id == msg.data['custom_id']:
            await mtoedit.edit(embed=discord.Embed(title="Coin Flip",description="You won {0} money!".format(bet),color=discord.Color.green()).set_footer(text=footer),view=None)
            user.add(author.id,"moneygained",bet)
            user.add(author.id,"wins",1)
            user.add(author.id,"money",bet)
            print("won")
        else:
            await mtoedit.edit(embed=discord.Embed(title="Coin Flip",description="You lost {0} money!".format(bet),color=discord.Color.red()).set_footer(text=footer),view=None)
            user.add(author.id,"moneylost",bet)
            user.add(author.id,"loss",1)
            user.add(author.id,"money",-bet)
            print("loss")

    @commands.hybrid_command(name='doubleornothing',aliases=['double','db'])
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    async def double(self, ctx:commands.Context) -> None:
        """bet = $50"""
        bet: int = 50
        if user.read(ctx.author,'money') < bet:
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

        bt: list[Button] = [Button(label='Double',custom_id='double'),Button(label='Cash Out',custom_id='cash',disabled=True)]
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
                await mtoedit.edit(embed=discord.Embed(
                        title="TimeoutError",
                        description="Sorry, you failed to respond in under 10 seconds so I gave up",
                        color=discord.Color.red()
                    ).set_footer(text=bcfg['footer']),
                    view=None
                )
                return
            
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
