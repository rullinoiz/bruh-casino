# https://github.com/Luffich/st-comunity-music/blob/main/music_rus.py

import discord
import time
import math
import asyncio
import itertools
import random
from discord import Interaction, Member
from discord.ext import commands
from bc_common.BruhCasinoEmbed import BruhCasinoEmbed
from modules.music.YTDLSource import YTDLSource
from modules.music.exceptions import VoiceError
from async_timeout import timeout

class Song:
    __slots__ = ("source", "requester", "startedplaying", "paused")

    def __init__(self, source: YTDLSource) -> None:
        self.source: YTDLSource = source
        self.startedplaying: float = time.time()
        self.paused: bool = False
        self.requester: Member = source.requester

    def pause(self) -> None:
        self.paused = True
        self.startedplaying = time.time() - self.startedplaying

    def unpause(self) -> None:
        self.paused = False
        self.startedplaying = time.time() - self.startedplaying

    def get_progress_bar(self, length: int = 32) -> list[str]:
        progress_bar = list("-" * length)
        progress = math.floor((((
            time.time() - self.startedplaying) if not self.paused else self.startedplaying) / self.source.duration) * len(
            progress_bar))
        progress_bar[:progress] = "=" * progress
        progress_bar[progress] = ">" if not self.paused else "|"

        return progress_bar

    def create_embed(self) -> discord.Embed:
        progress_bar: list[str] = self.get_progress_bar()

        where = YTDLSource.parse_duration(
            (time.time() - self.startedplaying) if not self.paused else self.startedplaying)
        duration = YTDLSource.parse_duration(self.source.duration)

        embed = (BruhCasinoEmbed(
            title="now playing" if not self.paused else "paused",
            description=f'[{self.source.title}]({self.source.url})\n```{where}{" " * (len(progress_bar) - len(where) - len(duration))}{duration}\n{"".join(progress_bar)}```',
            color=discord.Color.blurple())
         .add_field(name="requested by", value=self.requester.mention)
         .add_field(name="uploaded by", value=f"[{self.source.uploader}]({self.source.uploader_url})" if self.source.uploader_url else f"{self.source.uploader}")
         .set_thumbnail(url=self.source.thumbnail)
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
    def __init__(self, bot: commands.Bot, ctx: Interaction) -> None:
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        # self.startedplaying = 0
        self.next = asyncio.Event()
        self.songs = SongQueue()
        self.exists = True

        self._loop = False
        self._autoplay = False
        self._volume = 0.5
        self.skip_votes = set()
        self.now = None

        self.audio_player = bot.loop.create_task(self.audio_player_task())

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
            self.next.clear()
            self.now = None
            try:
                if len(self.voice.channel.members) == 1:
                    # noinspection PyAsyncCall
                    self.bot.loop.create_task(self.stop())
                    self.exists = False
                    return
            except:
                pass

            if not self.loop:
                # If autoplay is turned on wait 3 seconds for a new song.
                # If no song is found find a new one,
                # else if autoplay is turned off try to get the
                # next song within 3 minutes.
                # If no song will be added to the queue in time,
                # the player will disconnect due to performance
                # reasons.

                # noinspection PyUnreachableCode
                if False:  # self.autoplay:
                    try:
                        async with timeout(3):
                            self.current = await self.songs.get()
                    except asyncio.TimeoutError:
                        # Spoof user agent to show whole page.
                        # headers = {'User-Agent' : 'Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)'}
                        song_url = self.current.source.url
                        api_base = 'https://www.googleapis.com/youtube/v3/search?part=snippet&relatedToVideoId={0}&type=video&key=AIzaSyAtllmETrA096Th6iQ_UL8WF-TrT0Au6-M'
                        api_base = api_base.format(song_url[-11:])
                        # Get the page
                        async with httpx.AsyncClient() as client:
                            response = await client.get(api_base)
                            response = json.loads(response.text)

                        # Parse all the recommended videos out of the response and store them in a list
                        # response = json.loads(response)
                        recommended_urls = []
                        for item in response['items']:
                            if item['id']['kind'] == 'youtube#video':
                                recommended_urls.append('https://youtube.com/watch?v=' + item['id']['videoId'])

                        ctx = self._ctx

                        # await ctx.send('we do a little loading')
                        try:
                            source = await YTDLSource.create_source(ctx, random.choice(recommended_urls),
                                                                    loop=self.bot.loop)
                        except YTDLError as e:
                            await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
                            self.bot.loop.create_task(self.stop())
                            self.exists = False
                            return
                        else:
                            song = Song(source)
                            self.current = song
                            await ctx.send('queued {}'.format(str(source)), delete_after=5)

                else:
                    try:
                        async with timeout(60):  # not 3 minutes
                            is_playing = len(self.songs) != 0 and self.current is not None
                            self.current = await self.songs.get()
                    except Exception as e:
                        print(e)
                        # noinspection PyAsyncCall
                        self.bot.loop.create_task(self.stop())
                        self.exists = False
                        return

                self.current.source.volume = self._volume
                self.voice.play(self.current.source, after=self.play_next_song)
                self.current.startedplaying = time.time()
                if is_playing:
                    await self.current.source.channel.send(
                        embed=self.current.create_embed())

            # If the song is looped
            elif self.loop:
                self.now = discord.FFmpegPCMAudio(self.current.source.stream_url, **YTDLSource.FFMPEG_OPTIONS)
                self.voice.play(self.now, after=self.play_next_song)
                self.current.startedplaying = time.time()

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
