# -*- coding: utf-8 -*-

import asyncio
import inspect
import logging
import os
import time
import traceback
from itertools import cycle
# noinspection PyUnresolvedReferences
from os import system as sys
from random import randint as random
from random import seed
from typing import Callable, Union

import discord
from discord.ext import commands, tasks

from bot_config import bot_config as bcfg
from modules.BruhCasinoError import BruhCasinoError
from modules.BruhCasinoEmbed import BruhCasinoEmbed
from modules.checks import is_developer, is_developer_predicate
from modules.exceptions import ArgumentError, MultipleInstanceError, AccessDenied, RateError
from modules.server import server
# noinspection PyUnresolvedReferences
from modules.user_instance import user_instance
from modules.user_sqlite import user as userdata

#to make sure random is pretty random
seed(time.time())

#epic settings
prefix = bcfg["prefix"]
footer = bcfg["footer"]
expincrement = bcfg["expincrement"]
expstart = bcfg["expstart"]

discord.utils.setup_logging(level=logging.WARNING)

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix=commands.when_mentioned_or(prefix), intents=intents)

statuses = cycle([f'{prefix}bruh',f'{prefix}daily','Raid Shadow Legends','cat compilation #132', 'Quake Live'])

@tasks.loop(seconds=300)
async def cycle_status() -> None:
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing,name=next(statuses)))

@client.event
async def on_ready() -> None:
    print('READY.')
    cycle_status.start()

@client.event
async def on_command_error(ctx: Union[commands.Context, discord.Interaction], e:commands.CommandError, *args, **kwargs) -> None:
    f = type(e)
    description: str
    # TODO: Refactor for 3.11 (when it comes out)
    if f == commands.MissingRequiredArgument:
        e = ArgumentError(ctx.command)
    elif f in [commands.CommandInvokeError, commands.HybridCommandError, discord.app_commands.CommandInvokeError, discord.ext.commands.ConversionError]:
        e = e.original
        if type(e) in [commands.CommandInvokeError, commands.HybridCommandError, discord.app_commands.CommandInvokeError]:
            e = e.original
        print(''.join(traceback.format_exception(type(e), e, e.__traceback__)))
    elif f == commands.MaxConcurrencyReached:
        e = MultipleInstanceError(ctx.command)
    elif f == commands.CommandOnCooldown:
        e = RateError(f"your ass is NOT spamming `/{ctx.command.name}` (please wait {e.retry_after} seconds)")

    codestyle: bool = getattr(e, 'codestyle', True)
    description = f'```{str(e)}```'
    if not isinstance(e, BruhCasinoError): description += '\nplease ping me about this error because it was not intentional'
    if not codestyle: description = description[3:-3]
    func: Callable

    embed: discord.Embed = BruhCasinoEmbed(
        title=type(e).__name__,
        description=description,
        color=discord.Color.red(),
    )

    if codestyle:
        embed.set_image(url="https://media1.tenor.com/m/7kFmSbAcLsUAAAAC/conductor-we-have-a-problem-cat.gif")

    if isinstance(ctx, discord.Interaction):
        return await ctx.response.send_message(
            embed=embed,
            ephemeral=True
        )
    else:
        func = (e.message.edit if (toedit := hasattr(e, 'message')) else ctx.send)

    await func(
        embed=embed,
        **({'view':None} if (toedit or isinstance(e, AccessDenied)) and not getattr(e, 'ephemeral', False) else {'view':None,'ephemeral':True})
    )

@client.event
async def on_message(message: discord.Message) -> None:
    if message.author == client.user or message.is_system():
        return

    if message.mention_everyone or client.user.mentioned_in(message):
        try:
            reaction = discord.utils.get(message.guild.emojis, name="ping")
            if reaction: await message.add_reaction(reaction)
        except AttributeError:
            pass

        print("pinged lmao")

    if not message.content.startswith(prefix) and "bruh" in message.content.lower():
        if server.read(message.guild.id,"bruhreact"):
            for i in "🇧""🇷""🇺""🇭": await message.add_reaction(i)

        x = message.content.lower().count('bruh')

        userdata.add(message.author.id,"bruh",x)
        print("bruh")
        return

    await client.process_commands(message)

    if prefix in message.content and prefix in list(message.content)[0]:
        base = message.content.split(" ")
        command = base[0].replace(prefix,"")
        base.remove(base[0])
        args = base
        channel = message.channel
        print("command received: " + str(prefix) + str(command) + " " + str(args) + " in channel {0}".format(channel))

    channel = message.channel
    author: user_instance = user_instance(message.author.id)
    if not message.author.bot:
        if author.read("lastmsg") < (time.time() - 30):
            author["lastmsg"] = time.time()
            author["exp"] += random(5, 15)
            author["money"] += bcfg["moneyexp"]

            if author.exp >= (author.lvl * expincrement) + expstart:
                userdata.c.execute(
                    "update user set exp = exp - (lvl * ?) + ?, lvl = lvl + 1, money = money + (lvl * 10) where id = ?",
                    (expincrement, expstart, author.id))
                print("level up")
                if server.read(channel.guild.id,'levelup_announce'):
                    await channel.send(
                        embed=discord.Embed(
                            title="Level Up!",
                            description=server.read(channel.guild.id,"levelmsg").replace("{user}","{0}".format(message.author.mention)).replace("{level}",str(author.lvl)) + "\n\n Check your next goal with `{0}level`".format(prefix),
                            color=discord.Color.green(),
                        ).set_footer(text=footer),
                        delete_after=None if server.read(channel.guild.id,'lingering_levelup') else 10
                    )

@client.event
async def on_reaction_add(reaction:discord.Reaction, user: discord.User) -> None:
    if reaction.message.author != client.user or reaction.emoji != '❌': return

    if is_developer_predicate(user): await reaction.message.delete()

@client.command(name='exec')
@is_developer()
async def _exec(ctx, *, script:str) -> None:
    """literally a backdoor"""

    # noinspection PyUnusedLocal
    author = ctx.author
    # noinspection PyUnusedLocal
    channel = ctx.channel
    message = ctx.message
    
    prg = script
    
    result = eval(prg)
    if inspect.isawaitable(result): await result
    await message.add_reaction("✅")
    return

async def load_extensions() -> None:
    for filename in os.listdir('cogs'):
        if filename.endswith('.py'):
            await client.load_extension(f'cogs.{filename[:-3]}')

async def main():
    async with client:
        print('BRUHBOT CONNECTING...')
        await load_extensions()
        await client.start(os.environ['BOT_TOKEN'])
asyncio.run(main())
