import asyncio
import discord
from discord.ext import commands
import time
import random
from typing import Optional
import os
import re
import tempfile
import modules.attorney as attorn

from discord.ext.commands.context import Context
from bot_config import bot_config as bcfg
from modules.server import server
from modules.user_instance import user_instance
from modules.checks import is_command_enabled, under_construction
from modules.exceptions import BrokeError

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
    'https://tenor.com/view/nerding-speech-bubble-pepe-nerd-gif-26077806',
    'https://media.discordapp.net/attachments/1061510650389606450/1092845311053004810/attachment-19.gif',

]

gif_reply = {
    'https://media.discordapp.net/attachments/769591923387269143/947381976015470682/IMG_1406.gif': {
        'content': 'https://media.discordapp.net/attachments/769591923387269143/947382042012823612/IMG_1407.gif',
        'replytome': False
    },
    'https://media.discordapp.net/attachments/806268326031917067/910886249756233748/image0-132-1.gif': {
        'content': 'https://tenor.com/view/cat-cat-cat-cat-cat-cat-cat-cat-cat-cat-catc-atca-gif-25291329',
        'replytome': False
    },

    'kys': 'https://media.discordapp.net/attachments/886495693626294312/1136808274478506024/image.gif',
    'kill yourself': 'https://media.discordapp.net/attachments/886495693626294312/1136808274478506024/image.gif'
}

class AttorneyComment:
    pattern = r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""

    def __init__(self, message: discord.Message) -> None:
        self.author = message.author
        self.body = re.sub(self.pattern, '[link]', message.content)
        self.score = 0

class TrollAlreadyArmed(commands.CommandError):
    def __init__(self, msg: str = 'troll already armed for this channel') -> None:
        self.msg = msg
        self.codestyle = False
        self.ephemeral = True
        super().__init__(msg)

class SnipeFailed(commands.CommandError):
    def __init__(self, msg: str = 'No deleted messages found for this channel!') -> None:
        self.msg = msg
        self.codestyle = False
        super().__init__(msg)

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.sniped: dict = {}
        self.nexttroll: dict = {}

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
            i in msg.content.lower() for i in ['genshin impact', 'league of legends', 'valorant', 'hunie pop', 'huniepop']
        )

    async def cog_before_invoke(self, ctx: Context) -> None:
        ctx.sniped = None
        if not isinstance(ctx.channel, discord.DMChannel):
            ctx.sniped = self.get_sniped(ctx.guild.id, ctx)
        ctx.stats = user_instance(ctx)

    @commands.Cog.listener()
    async def on_message_delete(self, msg: discord.Message) -> None:
        if msg.author == self.bot.user or msg.is_system() or isinstance(msg.channel, discord.DMChannel) or msg.author.bot: return
        self.set_sniped(msg)
        if server.read(msg.guild.id, 'i_saw_what_you_deleted'):
            await msg.channel.send('https://tenor.com/view/i-saw-what-you-deleted-cat-gif-25407007')

        msgafter: list[discord.Message] = [i async for i in msg.channel.history(limit=1, after=msg)]
        for i in msgafter:
            if i.author == self.bot.user and any([c in i.content for c in bubble_gifs]):
                await i.delete()
                return

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message) -> None:
        if msg.author == self.bot.user or msg.is_system() or isinstance(msg.channel, discord.DMChannel) or bcfg['prefix'] in msg.content:
            return
        if (not (msg.is_system() or msg.author.bot) and server.read(msg.guild.id, 'speech_bubble') and random.randint(1,100) == 69) or self.nexttroll.get(msg.channel.id, False):
            await msg.channel.send(content=random.choice(bubble_gifs))
            print('trolled')
            if self.nexttroll.get(msg.channel.id): del self.nexttroll[msg.channel.id]
        else:
            for i in gif_reply.keys():
                if i.lower() in msg.content.lower():
                    await (msg.reply if (False if type(gif_reply[i]) is str else gif_reply[i]['replytome']) else msg.channel.send)(content=gif_reply[i] if type(gif_reply[i]) is str else gif_reply[i]['content'])

            if server.read(msg.guild.id, 'lowtiergod') and self.lowtiergod(msg):
                await msg.reply('https://tenor.com/view/low-tier-god-awesome-mario-twerking-gif-23644561')

        # print([i.to_dict() for i in msg.embeds])
        # print([i.url for i in msg.attachments])

    @commands.hybrid_command()
    @is_command_enabled(command='troll')
    @commands.guild_only()
    async def troll(self, ctx: Context) -> None:
        """epicly troll next messager in this channel for 200 money"""
        price: int = 200

        if ctx.stats.money < price:
            raise BrokeError(price, ctx.stats.money)
        if self.nexttroll.get(ctx.channel.id):
            raise TrollAlreadyArmed()

        ctx.stats.money -= price
        self.nexttroll[ctx.channel.id] = ctx.author.id

        await ctx.send('troll now armed', ephemeral=True)
        print(f'troll armed in channel {ctx.channel} by {ctx.author}')

    @commands.hybrid_command()
    @is_command_enabled(command='snipe')
    @commands.guild_only()
    async def snipe(self, ctx: Context) -> None:
        if msg := ctx.sniped:
            embed = discord.Embed(
                description=msg.content
            ).set_author(name=msg.author.name,icon_url=msg.author.display_avatar.url).set_footer(text=bcfg['footer'])
        else:
            raise SnipeFailed()
        
        await ctx.send(embed=embed,delete_after=None if msg else 7)

    @commands.hybrid_command()
    @commands.max_concurrency(1, per=commands.BucketType.channel, wait=False)
    async def attorney(
            self,
            ctx: Context,
            last_messages: commands.Range[int, 3, 50],
            channel: Optional[discord.TextChannel] = None) -> None:
        users: dict = {}
        messages: list[AttorneyComment] = []
        _channel = channel or ctx.channel

        await ctx.defer()

        async for i in _channel.history(limit=last_messages):
            if i.content is None or i.content == '': continue
            if i.author.name not in users.keys(): users[i.author.name] = 1
            else: users[i.author.name] += 1
            messages.insert(0, AttorneyComment(i))

        users: list = sorted(users, reverse=True)
        scenes = await asyncio.to_thread(attorn.comments_to_scene, messages, attorn.get_characters(users))
        mtoedit = await ctx.send('compiling video...')
        video = await attorn.ace_attorney_anim(
            scenes,
            vid := tempfile.NamedTemporaryFile(suffix='.mp4'),
            aud := tempfile.NamedTemporaryFile(suffix='.mp3'),
            file := str(_channel.id) + '.mp4',
            logfile := open((log := tempfile.NamedTemporaryFile()).name,'r+b')
        )

        while video.returncode is None:
            await asyncio.sleep(1)
            logread = str(log.read())[2:-1].replace('\\n','\n')
            await mtoedit.edit(content='```'+logread[max(0, len(logread)-500):]+'```')

        await video.wait()
        print('video done')

        await mtoedit.edit(
            content='(big thanks to https://github.com/micah5/ace-attorney-reddit-bot/blob/master/anim.py)',
            attachments=[discord.File(file, filename='attorney.mp4')],
            embed=None
        )

        logfile.close()
        os.remove(file)

    @commands.command()
    @under_construction()
    async def please(self,
                     ctx: Context,
                     verb: str,
                     pronoun: str,
                     noun: Optional[str],
                     *, adverbs: Optional[str]) -> None:
        sentence: str = ''
        sentence += f'consider {pronoun} '
        if noun: sentence += f'{noun.removesuffix(",").replace("me", "you").replace("my", "your")} '
        if not (adverbs and ' ' not in adverbs): sentence += f'{verb.removesuffix("e")}ed '
        if adverbs and not (noun and noun.endswith(',')): sentence += f'{adverbs.split(",")[0]} '
        if adverbs and ' ' not in adverbs: sentence += f'{verb.removesuffix("e")}ed'

        await ctx.send(sentence.replace('@everyone','\\@everyone'))


    @commands.hybrid_command()
    @commands.max_concurrency(1, per=commands.BucketType.channel, wait=False)
    @under_construction()
    async def attorney_new(self,
                       ctx: Context,
                       last_messages: int = 20,
                       channel: Optional[discord.TextChannel] = commands.parameter(default=lambda ctx: ctx.channel)) -> None:
        pass

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Fun(bot))
    print('Fun loaded')
