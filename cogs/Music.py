import asyncio
import functools
import itertools
import math
import random
import os
import typing
import time
import math
import modules.exceptions as exceptions
import json

import discord
import yt_dlp as youtube_dl
from async_timeout import timeout
from discord.ext import commands
from discord import app_commands
import httpx
from bs4 import BeautifulSoup

from modules.checks import is_developer
from bot_config import bot_config as bcfg

discord.opus.load_opus(name=('/opt/homebrew/Cellar/opus/1.3.1/lib/libopus.dylib' if os.uname().sysname == 'Darwin' else '/usr/lib/aarch64-linux-gnu/libopus.so.0')) 

# Silence useless bug reports messages
youtube_dl.utils.bug_reports_message = lambda: ''


class VoiceError(commands.CommandError):
    def __init__(self, msg:str, codestyle:bool=True) -> None:
        self.msg = msg
        self.codestyle = codestyle
        super().__init__(msg)

class YTDLError(commands.CommandError):
    def __init__(self, msg:str, codestyle:bool=True) -> None:
        self.msg = msg
        self.codestyle = codestyle
        super().__init__(msg)

class SongTooLong(commands.CommandError):
    def __init__(self, msg:str='that song is too long for me', codestyle:bool=False) -> None:
        self.msg = msg
        self.codestyle = codestyle
        super().__init__(msg)

class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'no_playlist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5) -> None:
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = int(data.get('duration'))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')

    def __str__(self) -> str:
        return '**{0.title}** by **{0.uploader}**'.format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None) -> typing.Union[object, list[object]]:
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))
        
        if '_type' in data.keys() and data['_type'] == 'playlist' and not data['webpage_url'].startswith('ytsearch'):
            if data['playlist_count'] > 20:
                raise exceptions.TooMuchData(f'Maximum playlist item count is 20! (received {data["playlist_count"]} songs)')
            
            sources = [cls(ctx,discord.FFmpegPCMAudio(x['url'],**cls.FFMPEG_OPTIONS),data=x) for x in data['entries']]
            return sources
            

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('Couldn\'t fetch `{}`'.format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError('Couldn\'t retrieve any matches for `{}`'.format(webpage_url))
        
        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

    @classmethod
    async def search_source(cls, bot, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        channel = ctx.channel
        loop = loop or asyncio.get_event_loop()

        cls.search_query = '%s%s:%s' % ('ytsearch', 10, ''.join(search))

        partial = functools.partial(cls.ytdl.extract_info, cls.search_query, download=False, process=False)
        info = await loop.run_in_executor(None, partial)

        cls.search = {}
        cls.search["title"] = f'Search results for:\n**{search}**'
        cls.search["type"] = 'rich'
        cls.search["color"] = 7506394
        cls.search["author"] = {'name': f'{ctx.author.name}', 'url': f'{ctx.author.display_avatar.url}', 'icon_url': f'{ctx.author.display_avatar.url}'}
        
        lst = []

        i = 1
        print('a')
        entries = list(info['entries'])
        for e in entries:
            #lst.append(f'`{info["entries"].index(e) + 1}.` {e.get("title")} **[{YTDLSource.parse_duration(int(e.get("duration")))}]**\n')
            VId = e.get('id')
            VUrl = 'https://www.youtube.com/watch?v=%s' % (VId)
            lst.append(f'`{i}.` [{e.get("title")}]({VUrl})\n')
            i += 1
        
        del i

        lst.append('\n**yype `cancel` to exit**')
        cls.search["description"] = "\n".join(lst)

        em = discord.Embed.from_dict(cls.search)
        await ctx.send(embed=em, delete_after=45.0)

        def check(msg):
            return msg.content.isdigit() == True and msg.channel == channel or msg.content == 'cancel' or msg.content == 'Cancel'
        
        try:
            m = await bot.wait_for('message', check=check, timeout=45.0)

        except asyncio.TimeoutError:
            rtrn = 'timeout'

        else:
            if m.content.isdigit() == True:
                sel = int(m.content)
                if 0 < sel <= 10:
                    """data = value[sel - 1]"""
                    value = entries
                    print('b')
                    print(value)
                    VId = list(value)[sel-1]['id']
                    VUrl = 'https://www.youtube.com/watch?v=%s' % (VId)
                    partial = functools.partial(cls.ytdl.extract_info, VUrl, download=False)
                    data = await loop.run_in_executor(None, partial)
                    rtrn = cls(ctx, discord.FFmpegPCMAudio(data['url'], **cls.FFMPEG_OPTIONS), data=data)
                else:
                    rtrn = 'sel_invalid'
            elif m.content == 'cancel':
                rtrn = 'cancel'
            else:
                rtrn = 'sel_invalid'
        
        return rtrn

    @staticmethod
    def parse_duration(duration: int) -> str:
        if duration > 0:
            # minutes, seconds = divmod(duration, 60)
            # hours, minutes = divmod(minutes, 60)
            # days, hours = divmod(hours, 24)

            # duration = []
            # if days > 0:
            #     duration.append('{}'.format(days))
            # if hours > 0:
            #     duration.append('{}'.format(hours))
            # if minutes > 0:
            #     duration.append('{}'.format(minutes))
            # if seconds > 0:
            #     duration.append('{}'.format(seconds))
            
            # value = ':'.join(duration)
            #print(duration)
            value = time.strftime('%H:%M:%S' if duration > 3600 else '%M:%S', time.gmtime(duration))
        
        elif duration == 0:
            value = "LIVE"
        
        return value


class Song:
    __slots__ = ('source', 'requester', 'startedplaying', 'paused')

    def __init__(self, source: YTDLSource) -> None:
        self.source = source
        self.startedplaying = time.time()
        self.paused = False
        self.requester = source.requester

    def pause(self) -> None:
        self.paused = True
        self.startedplaying = time.time() - self.startedplaying

    def unpause(self) -> None:
        self.paused = False
        self.startedplaying = time.time() - self.startedplaying
    
    def create_embed(self) -> discord.Embed:
        progress_bar = list('-'*32)
        progress = math.floor((((time.time()-self.startedplaying) if not self.paused else self.startedplaying)/self.source.duration)*len(progress_bar))
        #print(progress)
        progress_bar[:progress] = '='*progress
        progress_bar[progress] = '>' if not self.paused else '|'

        where = YTDLSource.parse_duration((time.time()-self.startedplaying) if not self.paused else self.startedplaying)
        duration = YTDLSource.parse_duration(self.source.duration)

        embed = (discord.Embed(title='now playing' if not self.paused else 'paused', description=f'[{self.source.title}]({self.source.url})\n```{where}{" "*(len(progress_bar)-len(where)-len(duration))}{duration}\n{"".join(progress_bar)}```', color=discord.Color.blurple())
            .add_field(name='requested by', value=self.requester.mention)
            .add_field(name='uploaded by', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
            .set_thumbnail(url=self.source.thumbnail)
            #.set_author(name=self.requester.name, icon_url=self.requester.display_avatar.url)
            .set_footer(text=bcfg['footer'])
        )
        return embed


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self) -> int:
        return self.qsize()

    def clear(self) -> None:
        self._queue.clear()

    def shuffle(self) -> None:
        random.shuffle(self._queue)

    def remove(self, index: int) -> None:
        del self._queue[index]


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context) -> None:
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        #self.startedplaying = 0
        self.next = asyncio.Event()
        self.songs = SongQueue()
        self.exists = True

        self._loop = False
        self._autoplay = False
        self._volume = 0.5
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())
        #print('voice state created')

    def __del__(self) -> None:
        self.audio_player.cancel()

    @property
    def loop(self) -> bool:
        return self._loop

    @loop.setter
    def loop(self, value: bool) -> None:
        self._loop = value

    @property
    def autoplay(self) -> bool:
        return self._autoplay

    @autoplay.setter
    def autoplay(self, value: bool) -> None:
        self._autoplay = value

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        self._volume = value

    @property
    def is_playing(self) -> bool:
        return self.voice and self.current and self.voice.is_playing()

    async def audio_player_task(self) -> None:
        while True:
            #print(1)
            self.next.clear()
            self.now = None
            #print('1.5')
            try:
                if len(self.voice.channel.members) == 1:
                    self.bot.loop.create_task(self.stop())
                    self.exists = False
                    return
            except:
                pass

            if self.loop == False:
                # If autoplay is turned on wait 3 seconds for a new song.
                # If no song is found find a new one,
                # else if autoplay is turned off try to get the
                # next song within 3 minutes.
                # If no song will be added to the queue in time,
                # the player will disconnect due to performance
                # reasons.
                if False:#self.autoplay:
                    try:
                        async with timeout(3): 
                            self.current = await self.songs.get()
                    except asyncio.TimeoutError:
                        # Spoof user agent to show whole page.
                        #headers = {'User-Agent' : 'Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)'}
                        song_url = self.current.source.url
                        api_base = 'https://www.googleapis.com/youtube/v3/search?part=snippet&relatedToVideoId={0}&type=video&key=AIzaSyAtllmETrA096Th6iQ_UL8WF-TrT0Au6-M'
                        api_base = api_base.format(song_url[-11:])
                        # Get the page
                        async with httpx.AsyncClient() as client:
                            response = await client.get(api_base)
                            response = json.loads(response.text)

                        # Parse all the recommended videos out of the response and store them in a list
                        #response = json.loads(response)
                        recommended_urls = []
                        for item in response['items']:
                            if item['id']['kind'] == 'youtube#video':
                                recommended_urls.append('https://youtube.com/watch?v='+item['id']['videoId'])

                        ctx = self._ctx

                        #await ctx.send('we do a little loading')
                        try:
                            source = await YTDLSource.create_source(ctx, random.choice(recommended_urls), loop=self.bot.loop)
                        except YTDLError as e:
                            await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
                            self.bot.loop.create_task(self.stop())
                            self.exists = False
                            return
                        else:
                            song = Song(source)
                            self.current = song
                            await ctx.send('queued {}'.format(str(source)),delete_after=5)
                        
                else:
                    try:
                        async with timeout(30):  # not 3 minutes
                            is_playing = not (len(self.songs) == 0 and self.current == None)
                            self.current = await self.songs.get()
                    except asyncio.TimeoutError:
                        self.bot.loop.create_task(self.stop())
                        self.exists = False
                        return
                
                #print(3)
                self.current.source.volume = self._volume
                self.voice.play(self.current.source, after=self.play_next_song)
                self.current.startedplaying = time.time()
                #print(4)
                if is_playing:
                    await self.current.source.channel.send(embed=self.current.create_embed().set_footer(text=bcfg['footer']))
            
            #If the song is looped
            elif self.loop == True:
                self.now = discord.FFmpegPCMAudio(self.current.source.stream_url, **YTDLSource.FFMPEG_OPTIONS)
                self.voice.play(self.now, after=self.play_next_song)
                self.current.startedplaying = time.time()
            
            #print(5)
            await self.next.wait()

    def play_next_song(self, error=None) -> None:
        if error:
            raise VoiceError(str(error))

        self.next.set()
    
    def pause(self) -> None:
        self.voice.pause()
        self.current.pause()

    def resume(self) -> None:
        self.voice.resume()
        self.current.unpause()

    def skip(self) -> None:
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self) -> None:
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context) -> VoiceState:
        state = self.voice_states.get(ctx.guild.id)
        if not state or not state.exists:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self) -> None:
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context) -> bool:
        if not ctx.guild:
            raise commands.NoPrivateMessage('errrm, you can\'t use that here')

        return True

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        ctx.voice_state = self.get_voice_state(ctx)

    # async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
    #     await ctx.send('something bad happened: {}'.format(str(error)))

    """@commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id != self.bot.user.id:
            print(f"{message.guild}/{message.channel}/{message.author.name}>{message.content}")
            if message.embeds:
                print(message.embeds[0].to_dict())"""

    @commands.hybrid_command(name='join', invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context) -> None:
        """Joins a voice channel."""

        await self.join(ctx)
        await ctx.send('joined',delete_after=5)

    async def join(self, ctx: commands.Context) -> None:
        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return #await ctx.send('joined',delete_after=5)

        ctx.voice_state.voice = await destination.connect()
        #await ctx.send('joined',delete_after=5)

    @commands.hybrid_command(name='summon')
    async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        """Summons the bot to a voice channel.
        If no channel was specified, it joins your channel.
        """

        if not channel and not ctx.author.voice:
            raise VoiceError('You are neither connected to a voice channel nor specified a channel to join.')

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return #await ctx.send('joined',delete_after=5)

        ctx.voice_state.voice = await destination.connect()
        #await ctx.send('joined',delete_after=5)

    @commands.hybrid_command(name='leave', aliases=['disconnect'])
    async def _leave(self, ctx: commands.Context) -> None:
        """Clears the queue and leaves the voice channel."""

        if not ctx.voice_state.voice:
            return await ctx.send('Not connected to any voice channel.')

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]
        await ctx.send('stopped',delete_after=5)

    @commands.hybrid_command(name='volume')
    @commands.check_any(commands.is_owner(),is_developer())
    async def _volume(self, ctx: commands.Context, *, volume: int) -> None:
        """Sets the volume of the player."""

        if not ctx.voice_state.is_playing:
            return await ctx.send('nothing is playing')

        if 0 > volume > 100:
            return await ctx.send('volume must be between 0 and 100')

        ctx.voice_state.volume = volume / 100
        await ctx.send('volume set to {}%'.format(volume))

    @commands.hybrid_command(name='now', aliases=['current', 'playing'])
    async def _now(self, ctx: commands.Context) -> None:
        """Displays the currently playing song."""
        if not ctx.voice_state.current:
            return await ctx.send('nothing is playing')
        embed = ctx.voice_state.current.create_embed()
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='pause', aliases=['pa'])
    async def _pause(self, ctx: commands.Context) -> None:
        """Pauses the currently playing song."""
        #print(">>>Pause Command:")
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.pause()
            await ctx.send('paused',delete_after=5)
            #await ctx.message.add_reaction('⏯')

    @commands.hybrid_command(name='resume', aliases=['re', 'res'])
    async def _resume(self, ctx: commands.Context) -> None:
        """Resumes a currently paused song."""

        if not ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.resume()
            await ctx.send('resumed',delete_after=5)
            #await ctx.message.add_reaction('⏯')

    @commands.hybrid_command(name='stop')
    async def _stop(self, ctx: commands.Context) -> None:
        """Stops playing song and clears the queue."""

        ctx.voice_state.songs.clear()

        if ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            await ctx.send('stopped',delete_after=5)
            #await ctx.message.add_reaction('⏹')

    @commands.hybrid_command(name='skip', aliases=['s'])
    async def _skip(self, ctx: commands.Context) -> None:
        """skip the song"""

        if not ctx.voice_state.is_playing:
            return await ctx.send('it\'s rather quiet')

        await ctx.send('skipping...')
        ctx.voice_state.skip()
        # voter = ctx.message.author
        # if voter == ctx.voice_state.current.requester:
        #     #await ctx.message.add_reaction('⏭')
        #     ctx.send('skipping...')
        #     ctx.voice_state.skip()

        # elif voter.id not in ctx.voice_state.skip_votes:
        #     ctx.voice_state.skip_votes.add(voter.id)
        #     total_votes = len(ctx.voice_state.skip_votes)

        #     if total_votes >= 3:
        #         await ctx.message.add_reaction('⏭')
        #         ctx.voice_state.skip()
        #     else:
        #         await ctx.send('Skip vote added, currently at **{}/3**'.format(total_votes))

        # else:
        #     await ctx.send('You have already voted to skip this song.')

    @commands.hybrid_command(name='queue')
    async def _queue(self, ctx: commands.Context, *, page: int = 1) -> None:
        """Shows the player's queue.
        You can optionally specify the page to show. Each page contains 10 elements.
        """

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('nothing in the queue')

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1, song)

        embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(len(ctx.voice_state.songs), queue))
                 .set_footer(text='page {}/{}'.format(page, pages)))
        await ctx.send(embed=embed)

    @commands.command(name='shuffle')
    async def _shuffle(self, ctx: commands.Context) -> None:
        """Shuffles the queue."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('nothing in the queue')

        ctx.voice_state.songs.shuffle()
        await ctx.send('shuffled',delete_after=5)
        #await ctx.message.add_reaction('✅')

    @commands.hybrid_command(name='remove')
    async def _remove(self, ctx: commands.Context, index: int) -> None:
        """Removes a song from the queue at a given index."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('nothing in the queue')

        ctx.voice_state.songs.remove(index - 1)
        await ctx.send('removed',delete_after=5)
        #await ctx.message.add_reaction('✅')

    @_remove.autocomplete('index')
    async def remove_autocomplete(self, ctx: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
        data = []
        for i, song in enumerate(self.voice_states.get(ctx.guild.id).songs, start=1):
            name = f'({i}) {song.source.title}'
            #print(name)
            if current.lower() in name.lower():
                data.append(app_commands.Choice(name=name, value=i))
        return data

    @commands.command(name='loop')
    async def _loop(self, ctx: commands.Context) -> None:
        """Loops the currently playing song.
        Invoke this command again to unloop the song.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('nothing is playing')

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = not ctx.voice_state.loop
        #await ctx.message.add_reaction('✅')
        await ctx.send('Looping is now turned ' + ('on' if ctx.voice_state.loop else 'off') )

    @commands.command(name='autoplay')
    async def _autoplay(self, ctx: commands.Context) -> None:
        """Automatically queue a new song that is related to the song at the end of the queue.
        Invoke this command again to toggle autoplay the song.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('nothing is playing')

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.autoplay = not ctx.voice_state.autoplay
        #await ctx.message.add_reaction('✅')
        await ctx.send('Autoplay is now ' + ('on' if ctx.voice_state.autoplay else 'off') )

    @commands.hybrid_command(name='play', aliases=['p'])
    async def _play(self, ctx, *, search: str) -> None:
        """Plays a song.
        If there are songs in the queue, this will be queued until the
        other songs finished playing.
        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
        """

        #await ctx.send('we do a little loading')
        await ctx.defer()
        source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
        if not ctx.voice_state.voice:
            await self.join(ctx)
        
        is_playing = ctx.voice_state.is_playing
        if type(source) == list:
            for i in source:
                song = Song(i)
                await ctx.voice_state.songs.put(song)
            await asyncio.sleep(1)
            return await ctx.send(content=f'queued {len(source)} songs',embed=None if is_playing else ctx.voice_state.current.create_embed())

        song = Song(source)
        await ctx.voice_state.songs.put(song)

        if is_playing:
            await ctx.send('queued {}'.format(str(source)))
        else:
            await ctx.send(embed=song.create_embed())
            
            
    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context) -> None:
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('connect to a voice channel first')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError('i\'m already in a voice channel')


async def setup(bot) -> None:
    await bot.add_cog(Music(bot))
