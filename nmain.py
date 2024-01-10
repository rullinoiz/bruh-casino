# -*- coding: utf-8 -*-
import discord
from discord.ext import commands,tasks
import time
from itertools import cycle
# noinspection PyUnresolvedReferences
from os import system as sys
from random import randint as random
from random import seed
import bot_config
from modules.server import server
from modules.user_sqlite import user as userdata
# noinspection PyUnresolvedReferences
from modules.user_instance import user_instance
from modules.exceptions import ArgumentError, MultipleInstanceError, AccessDenied
from modules.checks import is_developer, is_developer_predicate
import os
import logging
import inspect
import traceback

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

    codestyle: bool = getattr(e, 'codestyle', True)
    description = f'```{str(e)}```'
    if codestyle: description += '\nplease ping me about this error because it was not intentional'
    if not codestyle: description = description[3:-3]
    await (e.message.edit if (toedit := hasattr(e, 'message')) else ctx.send)(
        embed=discord.Embed(
            title=type(e).__name__,
            description=description,
            color=discord.Color.red(),
        ).set_footer(text=footer),
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
    else:
        channel = message.channel
        author = message.author
        if not author.bot:
            if userdata.read(author.id,"lastmsg") < (time.time() - 30):
                userdata.write(author.id,"lastmsg",time.time())
                userdata.add(author.id,"exp",random(5,15))

                if userdata.read(author.id,"exp") >= (userdata.read(author.id,"lvl") * expincrement) + expstart:
                    userdata.write(author.id,"exp",userdata.read(author.id,"exp") - ((userdata.read(author.id,"lvl") * expincrement) + expstart))
                    userdata.add(author.id,"lvl",1)
                    
                    print("level up")
                    if server.read(channel.guild.id,'levelup_announce'):
                        await channel.send(
                            embed=discord.Embed(
                                title="Level Up!",
                                description=server.read(channel.guild.id,"levelmsg").replace("{user}","{0}".format(author.mention)).replace("{level}",str(userdata.read(author.id,"lvl"))) + "\n\n Check your next goal with `{0}level`".format(prefix),
                                color=discord.Color.green(),
                            ).set_footer(text=footer),
                            delete_after=None if server.read(channel.guild.id,'lingering_levelup') else 10
                        )

@client.event
async def on_reaction_add(reaction:discord.Reaction, user: discord.User) -> None:
    print(reaction, user)
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

    #if not author.id == bcfg['le_admin']:
    #    raise AccessDenied(command)
    
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
