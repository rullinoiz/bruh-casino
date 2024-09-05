import time

import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
from discord import app_commands, Interaction
from discord.app_commands import Transform
import modules.cards as cards
from modules.user.user_sqlite import user
from bot_config import bot_config as bcfg
from modules.videopoker.videopoker import HandAnalyzer
from bc_common.BruhCasinoCog import EconomyBruhCasinoCog
from bc_common.BruhCasinoEmbed import BruhCasinoEmbed
from bc_common.BruhCasinoGame import BruhCasinoGame
from cogs.games_deps.DoubleOrNothing import DoubleOrNothingGame
from cogs.games_deps.Blackjack import BlackjackGame
from cogs.games_deps.Mines import MinesGame
from cogs.games_deps.SecretLair import SecretLairGame
from typing import Callable

import modules.checks as checks
from modules.transformers import Money
import modules.exceptions as e

import asyncio
from random import randint as random

class Games(EconomyBruhCasinoCog):

    async def setup_game(self, ctx: Interaction) -> None:
        game: dict[int, BruhCasinoGame] = getattr(self, f"{ctx.command.callback.__name__}_games")
        if ctx.user.id in game.keys():
            t: BruhCasinoGame = game[ctx.user.id]
            if t.active:
                raise e.MultipleInstanceError(ctx.command.name)
            t.view.stop()
            try:
                await t.message.edit(view=None)
            except AttributeError:
                pass
            game.__delitem__(ctx.user.id)

    @tasks.loop(seconds=5)
    async def garbage_collect(self) -> None:
        t: list[dict[int, BruhCasinoGame]] = [self.double_games, self.blackjack_games, self.mines_games, self.secretlair_games]

        for entry in t:
            to_delete: list[int] = []
            for u in entry.keys():
                game: BruhCasinoGame = entry[u]
                if not game.active and not hasattr(game, "message") and game.lastactive + 30 < time.time():
                    print(f"clearing {u} -> {game.__str__()}")
                    to_delete.append(u)
            for x in to_delete:
                entry.__delitem__(x)

    def __init__(self, bot: discord.ext.commands.Bot) -> None:
        super().__init__(bot)
        self.garbage_collect.start()
        self.double_games: dict[int, DoubleOrNothingGame] = {}
        self.blackjack_games: dict[int, BlackjackGame] = {}
        self.mines_games: dict[int, MinesGame] = {}
        self.secretlair_games: dict[int, SecretLairGame] = {}

    @app_commands.command(name="blackjack")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def blackjack(self, ctx: Interaction, bet: Transform[int, Money]) -> None:
        """blackjack gaming"""

        bet: int = int(bet)

        await self.setup_game(ctx)
        self.blackjack_games[ctx.user.id] = await BlackjackGame.create(self, ctx, bet, getbuttons=False, timeout=30)

    @app_commands.command(name='war')
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    @checks.under_construction()
    async def war(self, ctx: commands.Context, ante: Transform[int, Money], tie: Transform[int, Money] = 0) -> None:
        """tie pays 12:1"""
        ante: int = int(ante)
        tie: int = int(tie)

        if ante + tie > ctx.stats.money:
            raise e.BrokeError(ante + tie, ctx.stats.money)

        deck: cards.Deck = cards.Deck()

        dealers: list[cards.Card] = [deck.draw()]
        users: list[cards.Card] = [deck.draw()]

        bt: list[Button] = [Button(label='Go to War! ($'+str(ante)+')'),Button(label='Surrender')]
        buttons = View(timeout=20)
        for x in bt: buttons.add_item(x) 

        if dealers[0].rank == users[0].rank:
            mtoedit: discord.Message = await ctx.send(embed=BruhCasinoEmbed(
                    title="War",
                    description="It's a tie!" + (f" Your tie paid ${tie*12}!" if tie != 0 else ""),
                    color=discord.Color.orange(),
                )
                .add_field(name="Dealer",value=dealers[0])
                .add_field(name="You",value=users[0]),
                view=buttons
            )

            ctx.stats.add(('money','moneygained','wins'),(tie*12,tie*12,1))

            try:
                msg = await self.wait_for_button(ctx=ctx, mtoedit=mtoedit, timeout=20)
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

    @commands.hybrid_command(name="flip")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    async def flip(self, ctx: commands.Context, bet: Transform[int, Money]) -> None:
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
            user.add(author.id,('moneygained','wins','money'),(bet, 1, bet))
            print("won")
        else:
            await mtoedit.edit(embed=BruhCasinoEmbed(title="Coin Flip",description="You lost {0} money!".format(bet),color=discord.Color.red()),view=None)
            user.add(author.id,('moneylost','loss','money'),(bet, 1, -bet))
            print("loss")

    @app_commands.command(name="doubleornothing")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def double(self, ctx: Interaction, bet: Transform[int, Money]) -> None:
        """hit x10 for, like, a lot of money"""

        bet: int = int(bet)

        await self.setup_game(ctx)
        self.double_games[ctx.user.id] = await DoubleOrNothingGame.create(self, ctx, bet, timeout=20)

    @commands.hybrid_command(name='videopoker')
    @checks.under_construction()
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

    @app_commands.command(name="mines")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def mines(self, ctx: Interaction, bet: Transform[int, Money], mines: int = 3) -> None:
        bet: int = int(bet)

        if bet < 100:
            raise e.ArgumentValueError(f"Argument \"bet\" must be at least {100}!")

        if mines < 1 or mines > 23:
            raise e.ArgumentValueError(f"Argument \"mines\" must within 1 and 23!")

        await self.setup_game(ctx)
        self.mines_games[ctx.user.id] = await MinesGame.create(self, ctx, bet, mines=mines, timeout=30)

    @app_commands.command(name="secretlair")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def secretlair(self, ctx: Interaction, bet: Transform[int, Money], danger: int = 1) -> None:
        bet: int = int(bet)

        if bet < 100:
            raise e.ArgumentValueError(f"Argument \"bet\" must be at least {100}!")
        if danger < 0 or danger > 3:
            raise e.ArgumentValueError(f"Argument \"danger\" must be between 0 and 3!")

        await self.setup_game(ctx)
        self.secretlair_games[ctx.user.id] = await SecretLairGame.create(self, ctx, bet, danger=danger, timeout=60)

setup: Callable = Games.setup
