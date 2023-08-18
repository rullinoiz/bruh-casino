import discord
from discord.ext import commands
import time
import random
import typing
import os

import modules.attorney as attorn

from discord.ext.commands.context import Context
from bot_config import bot_config as bcfg

from modules.server import server
from modules.checks import is_command_enabled, under_construction

random.seed(time.time_ns())

bubble_gifs: list[str] = [
    'https://media.discordapp.net/attachments/730143781898420254/977732173186609192/606CB705-3CB9-4BB5-BE9D-94964B8A64FA.gif',
    'https://tenor.com/view/discord-gif-26012800',
    'https://media.discordapp.net/attachments/929807268994744340/1028946893960650762/bimplyactvity.gif',
    'https://media.discordapp.net/attachments/1031031024332845097/1056031662024163338/E8F3161A-6A5C-4E3B-A3EA-9EDB92681134.gif',
    'https://media.discordapp.net/attachments/1031031024332845097/1056031827384619068/B1AEA904-12DC-4222-A2A4-099D4245BA6D.gif',
    'https://media.discordapp.net/attachments/1031031024332845097/1056031855876526170/561AF173-2061-4ADE-B83B-A29EE3FC536A.gif',
    'https://media.discordapp.net/attachments/995114602503352350/1008560184316141578/gorilla_bird.gif',
    'https://media.discordapp.net/attachments/680019398047694869/939041225145720872/9AC9777C-E15F-48A9-9E99-4DA42ADD5236.gif',
    'https://media.discordapp.net/attachments/334296645833326604/1047543148336906300/bulldozer-1.gif',
    'https://media.discordapp.net/attachments/769591923387269143/1040494712555048960/IMG_3159.gif',
    'https://media.discordapp.net/attachments/1031031024332845097/1034609086098059344/488DC4BF-A959-4203-B49A-A9DA2315ACC6.gif',
    'https://media.discordapp.net/attachments/967921224179146752/1034340235271749632/hearsay.gif',
    #'https://media.discordapp.net/attachments/940088335723028551/998313082948440204/unknown-4.gif',
    'https://media.discordapp.net/attachments/769591923387269143/1028001612133847180/5B3539AE-D9E9-4008-97AF-70DCF6BF160B.gif',
    'https://tenor.com/view/franzj-dancing-gif-26197176',
    'https://media.discordapp.net/attachments/881636430940635146/988560915119079424/used.gif',
    'https://media.discordapp.net/attachments/885710706350116915/954043954045796392/2A73A57F-94BD-4BEC-B833-2BF2B604018B.gif',
    'https://tenor.com/view/nerding-speech-bubble-pepe-nerd-gif-26077806'
]

class AttorneyComment:
    def __init__(self, message: discord.Message) -> None:
        self.author = message.author
        self.body = message.content
        self.score = 0

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.sniped: dict = {}

    def get_sniped(self, _id: int, ctx:Context=None):
        if not self.sniped.get(_id):
            self.sniped[_id]: dict = {}

        if ctx:
            return self.sniped[_id].get(ctx.channel.id)
        return self.sniped[_id]
    
    def set_sniped(self, msg: discord.Message) -> None:
        self.get_sniped(msg.guild.id)
        self.sniped[msg.guild.id][msg.channel.id] = msg

    @staticmethod
    def lowtiergod(msg: discord.Message) -> bool:
        return any(
            i in msg.content for i in ['genshin impact', 'league of legends', 'valorant']
        )

    async def cog_before_invoke(self, ctx: Context) -> None:
        ctx.sniped = self.get_sniped(ctx.guild.id, ctx)

    @commands.Cog.listener()
    async def on_message_delete(self, msg: discord.Message) -> None:
        if msg.author == self.bot.user or msg.is_system() or msg.author.bot: return
        self.set_sniped(msg)
        if server.read(msg.guild.id, 'i_saw_what_you_deleted'):
            await msg.channel.send('https://tenor.com/view/i-saw-what-you-deleted-cat-gif-25407007')

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message) -> None:
        if msg.author == self.bot.user or msg.is_system() or isinstance(msg.channel, discord.DMChannel) or bcfg['prefix'] in msg.content:
            return
        if not (msg.is_system() or msg.author.bot) and server.read(msg.guild.id, 'speech_bubble') and random.randint(1,100) == 69:
            await msg.channel.send(content=random.choice(bubble_gifs))
            print('trolled')
        else:
            if 'https://media.discordapp.net/attachments/769591923387269143/947381976015470682/IMG_1406.gif' in msg.content:
                await msg.channel.send('https://media.discordapp.net/attachments/769591923387269143/947382042012823612/IMG_1407.gif')
            elif server.read(msg.guild.id, 'lowtiergod') and self.lowtiergod(msg):
                await msg.reply('https://tenor.com/view/low-tier-god-awesome-mario-twerking-gif-23644561')

    @commands.hybrid_command()
    @is_command_enabled(command='snipe')
    async def snipe(self, ctx: Context) -> None:
        if msg := ctx.sniped:
            embed = discord.Embed(
                description=msg.content
            ).set_author(name=msg.author.name,icon_url=msg.author.display_avatar.url).set_footer(text=bcfg['footer'])
        else:
            embed = discord.Embed(
                title='Snipe Failed',
                description='No deleted messages found for this channel!',
                color=discord.Color.red()
            ).set_footer(text=bcfg['footer'])
        
        await ctx.send(embed=embed,delete_after=None if msg else 7)

    @commands.hybrid_command()
    @commands.max_concurrency(1, per=commands.BucketType.channel, wait=False)
    async def attorney(self, ctx: Context, last_messages: int=20, channel: discord.TextChannel = None) -> None:
        users: dict = {}
        messages: list[AttorneyComment] = []
        _channel = channel or ctx.channel

        async for i in _channel.history(limit=last_messages, oldest_first=True):
            if i.content is None or i.content == '': continue
            if i.author.name not in users.keys():users[i.author.name] = 1
            else: users[i.author.name] += 1
            messages.append(AttorneyComment(i))

        users: list = sorted(users, reverse=True)
        await ctx.defer()
        await ctx.send(file=discord.File(attorn.comments_to_scene(messages, attorn.get_characters(users), file := str(ctx.channel.id) + '.mp4'), filename='attorney.mp4'))
        os.remove(file)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Fun(bot))
    print('Fun loaded')