# -*- coding: utf-8 -*-
import discord
from discord.ext import commands,tasks
import time
from itertools import combinations,cycle
from os import system as sys
from random import randint as random
from random import seed
from discord.utils import get as dget
import bot_config
from modules.server import server
from modules.user_sqlite import user
from modules.exceptions import ArgumentError, MultipleInstanceError
from modules.checks import is_developer
import os
import logging
import inspect

import asyncio

#to make sure random is pretty random
seed(time.time())

#epic settings
prefix = bot_config.bot_config["prefix"]
footer = bot_config.bot_config["footer"]
expincrement = bot_config.bot_config["expincrement"]
expstart = bot_config.bot_config["expstart"]

#secret wolfram settings (secret!! :flushed:)
app_id = "GTVE5T-93GHW98RLT"

discord.utils.setup_logging(level=logging.WARNING)

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix=commands.when_mentioned_or(prefix), intents=intents)

statuses = cycle([f'{prefix}bruh',f'{prefix}daily','Raid Shadow Legends','cat compilation #132'])

@tasks.loop(seconds=300)
async def cycle_status() -> None:
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing,name=next(statuses)))

@client.event
async def on_ready() -> None:
    print('READY.')
    cycle_status.start()

# @client.event
# async def on_error(event, *args, **kwargs) -> None:
#     print(args)
#     print(event)
#     await args[0].channel.send(embed=discord.Embed(
#             title=type(e.original).__name__,
#             description=f'Command "{e.command}" returned an error:```{str(e.original)}```',
#             color=discord.Color.red()
#         ).set_footer(text=footer)
#     )

@client.event
async def on_command_error(ctx:commands.Context, e:commands.CommandError) -> None:
    f = type(e)
    if f == commands.MissingRequiredArgument:
        e = ArgumentError(ctx.command)
    elif f in [commands.CommandInvokeError, commands.HybridCommandError, discord.app_commands.CommandInvokeError]:
        e = e.original
        if type(e) in [commands.CommandInvokeError, commands.HybridCommandError, discord.app_commands.CommandInvokeError]:
            e = e.original
    elif f == commands.MaxConcurrencyReached:
        e = MultipleInstanceError(ctx.command)

    codestyle = True if not hasattr(e, 'codestyle') else e.codestyle
    description = f'```{str(e)}```'
    if not codestyle: description = description[3:-3]
    await ctx.send(embed=discord.Embed(
            title=type(e).__name__,
            description=description,
            color=discord.Color.red()
        ).set_footer(text=footer)
    )

@client.event
async def on_message(message) -> None:
    if message.author == client.user or message.is_system():
        return

    if message.mention_everyone or client.user.mentioned_in(message):
        try:
            await message.add_reaction(discord.utils.get(message.guild.emojis,name="ping"))
        except:
            print("ping emoji not found")
        print("pinged lmao")

    if not message.content.startswith(prefix) and "bruh" in message.content.lower():
        if server.read(message.guild.id,"bruhreact") == True:
            await message.add_reaction("🇧")
            await message.add_reaction("🇷")
            await message.add_reaction("🇺")
            await message.add_reaction("🇭")

        x = 0

        for i in message.content.split(" "):
            if "bruh" in i.lower():
                x += 1

        user.add(message.author.id,"bruh",x)
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
    else:
        channel = message.channel
        author = message.author
        if not author.bot:
            if user.read(author.id,"lastmsg") < (time.time() - 30):
                user.write(author.id,"lastmsg",time.time())
                user.add(author.id,"exp",random(5,15))
                
                print("message counted")
                
                if user.read(author.id,"exp") >= (user.read(author.id,"lvl") * expincrement) + expstart:
                    user.write(author.id,"exp",user.read(author.id,"exp") - ((user.read(author.id,"lvl") * expincrement) + expstart))
                    user.add(author.id,"lvl",1)
                    
                    print("level up")
                    await channel.send(
                        embed=discord.Embed(
                            title = "Level Up!",
                            description = server.read(channel.guild.id,"levelmsg").replace("{user}","<@{0}>".format(author.id)).replace("{level}",str(user.read(author.id,"lvl"))) + "\n\n Check your next goal with `{0}level`".format(prefix),
                            color=discord.Color.green(),
                        ).set_footer(text=footer),
                        delete_after=10
                    )

@client.command(name='exec')
@is_developer()
async def _exec(ctx, *, script:str) -> None:
    """literally a backdoor"""

    author = ctx.author
    channel = ctx.channel
    message = ctx.message

    #if not author.id == bcfg['le_admin']:
    #    raise AccessDenied(command)
    
    prg = script
    
    result = eval(prg)
    if inspect.isawaitable(result):
        result = await result
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
