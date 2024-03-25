import discord
import asyncio
import os
import typing
import math

from discord.ext import commands
from discord import app_commands

from modules.BruhCasinoCog import BruhCasinoCog
from modules.music.exceptions import *
from modules.music.YTDLSource import YTDLSource
from modules.music.common import VoiceState, Song

from modules.checks import is_developer

discord.opus.load_opus(name=('/opt/homebrew/lib/libopus.dylib' if os.uname().sysname == 'Darwin' else '/usr/lib/aarch64-linux-gnu/libopus.so.0'))

# Silence useless bug reports messages
# youtube_dl.utils.bug_reports_message = lambda: ''

@app_commands.guild_only
class Music(BruhCasinoCog):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
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

    @commands.hybrid_group(with_app_command=True)
    @commands.guild_only()
    async def music(self, ctx: commands.Context) -> None: pass

    @music.command(name='join', invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context) -> None:
        """Joins a voice channel."""

        await self.join(ctx)
        await ctx.send('joined',delete_after=5)

    @staticmethod
    async def join(ctx: commands.Context) -> None:
        destination: discord.VoiceChannel = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @music.command(name='summon')
    async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        """Summons the bot to a voice channel.
        If no channel was specified, it joins your channel.
        """

        if not channel and not ctx.author.voice:
            raise VoiceError('You are neither connected to a voice channel nor specified a channel to join.')

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()
        await ctx.send('joined', ephemeral=True)

    @music.command(name='leave', aliases=['disconnect'])
    async def _leave(self, ctx: commands.Context) -> None:
        """Clears the queue and leaves the voice channel."""

        if not ctx.voice_state.voice:
            await ctx.send('Not connected to any voice channel.')
            return

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]
        await ctx.send('stopped',delete_after=5)

    @music.command(name='volume')
    @commands.check_any(commands.is_owner(),is_developer())
    async def _volume(self, ctx: commands.Context, *, volume: int) -> None:
        """Sets the volume of the player."""

        if not ctx.voice_state.is_playing:
            await ctx.send('nothing is playing')
            return

        if 0 > volume > 100:
            await ctx.send('volume must be between 0 and 100')
            return

        ctx.voice_state.volume = volume / 100
        await ctx.send('volume set to {}%'.format(volume))

    @music.command(name='now', aliases=['current', 'playing'])
    async def _now(self, ctx: commands.Context) -> None:
        """Displays the currently playing song."""
        if not ctx.voice_state.current:
            await ctx.send('nothing is playing')
            return
        embed = ctx.voice_state.current.create_embed()
        await ctx.send(embed=embed)

    @music.command(name='pause', aliases=['pa'])
    async def _pause(self, ctx: commands.Context) -> None:
        """Pauses the currently playing song."""
        #print(">>>Pause Command:")
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.pause()
            await ctx.send('paused',delete_after=5)
            #await ctx.message.add_reaction('⏯')

    @music.command(name='resume', aliases=['re', 'res'])
    async def _resume(self, ctx: commands.Context) -> None:
        """Resumes a currently paused song."""

        if not ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.resume()
            await ctx.send('resumed',delete_after=5)
            #await ctx.message.add_reaction('⏯')

    @music.command(name='stop')
    async def _stop(self, ctx: commands.Context) -> None:
        """Stops playing song and clears the queue."""

        ctx.voice_state.songs.clear()

        if ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            await ctx.send('stopped',delete_after=5)
            #await ctx.message.add_reaction('⏹')

    @music.command(name='skip', aliases=['s'])
    async def _skip(self, ctx: commands.Context) -> None:
        """skip the song"""

        if not ctx.voice_state.is_playing:
            await ctx.send('it\'s rather quiet')
            return

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

    @music.command(name='queue')
    async def _queue(self, ctx: commands.Context, *, page: int = 1) -> None:
        """Shows the player's queue.
        You can optionally specify the page to show. Each page contains 10 elements.
        """

        if len(ctx.voice_state.songs) == 0:
            await ctx.send('nothing in the queue')
            return

        items_per_page: int = 10
        pages: int = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start: int = (page - 1) * items_per_page
        end: int = start + items_per_page

        queue: str = ''
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1, song)

        embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(len(ctx.voice_state.songs), queue))
                 .set_footer(text='page {}/{}'.format(page, pages)))
        await ctx.send(embed=embed)

    @music.command(name='shuffle')
    async def _shuffle(self, ctx: commands.Context) -> None:
        """Shuffles the queue."""

        if len(ctx.voice_state.songs) == 0:
            await ctx.send('nothing in the queue')
            return

        ctx.voice_state.songs.shuffle()
        await ctx.send('shuffled',delete_after=5)
        #await ctx.message.add_reaction('✅')

    @music.command(name='remove')
    async def _remove(self, ctx: commands.Context, index: int) -> None:
        """Removes a song from the queue at a given index."""

        if len(ctx.voice_state.songs) == 0:
            await ctx.send('nothing in the queue')
            return

        ctx.voice_state.songs.remove(index - 1)
        await ctx.send('removed',delete_after=5)
        #await ctx.message.add_reaction('✅')

    @_remove.autocomplete('index')
    async def remove_autocomplete(self, ctx: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
        data = []
        for i, song in enumerate(self.voice_states.get(ctx.guild.id).songs, start=1):
            if current.lower() in (name := f'({i}) {song.source.title}').lower():
                data.append(app_commands.Choice(name=name, value=i))
        return data

    @music.command(name='loop')
    async def _loop(self, ctx: commands.Context) -> None:
        """Loops the currently playing song.
        Invoke this command again to unloop the song.
        """

        if not ctx.voice_state.is_playing:
            await ctx.send('nothing is playing')
            return

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = not ctx.voice_state.loop
        #await ctx.message.add_reaction('✅')
        await ctx.send('Looping is now turned ' + ('on' if ctx.voice_state.loop else 'off'))

    @commands.command(name='autoplay')
    async def _autoplay(self, ctx: commands.Context) -> None:
        """Automatically queue a new song that is related to the song at the end of the queue.
        Invoke this command again to toggle autoplay the song.
        """

        if not ctx.voice_state.is_playing:
            await ctx.send('nothing is playing')
            return

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.autoplay = not ctx.voice_state.autoplay
        #await ctx.message.add_reaction('✅')
        await ctx.send('Autoplay is now ' + ('on' if ctx.voice_state.autoplay else 'off'))

    @music.command(name='play', aliases=['p'])
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    async def _play(self, ctx: commands.Context, *, search: str) -> None:
        """Plays a song.
        If there are songs in the queue, this will be queued until the
        other songs finished playing.
        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
        """
        if not ctx.interaction: await ctx.send('we do a little loading')
        await ctx.defer()
        source: typing.Union[YTDLSource, list[YTDLSource]] = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
        if not ctx.voice_state.voice:
            await self.join(ctx)
        
        is_playing: bool = ctx.voice_state.voice.is_playing()
        was_playing: bool = ctx.voice_state.current is not None
        print(was_playing)
        if type(source) is list:
            for i in source:
                song: Song = Song(i)
                await ctx.voice_state.songs.put(song)

            await asyncio.sleep(1)
            await ctx.send(content=f'queued {len(source)} songs')
            return

        song = Song(source)
        await ctx.voice_state.songs.put(song)

        if is_playing:
            await ctx.send(f'queued [{str(source)}]({source.url})')
        elif not was_playing:
            await ctx.send(embed=song.create_embed())

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context) -> None:
        if (not ctx.author.voice or not ctx.author.voice.channel) and not ctx.voice_client:
            raise VoiceError('connect to a voice channel first')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise VoiceError('i\'m already in a voice channel')


async def setup(bot) -> None:
    await bot.add_cog(Music(bot))
    print('Music loaded')
