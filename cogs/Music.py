# https://github.com/Luffich/st-comunity-music/blob/main/music_rus.py
# This code has been heavily modified and refactored into different files
# You can find the rest of it in /modules/music/

import discord
import asyncio
import os
import typing
import math

from discord.ext import commands
from discord import app_commands, Interaction, VoiceProtocol

from bc_common.BruhCasinoCog import BruhCasinoCog
from modules.music.exceptions import *
from modules.music.YTDLSource import YTDLSource
from modules.music.common import VoiceState, Song

from modules.checks import is_developer

discord.opus.load_opus(name=("/opt/homebrew/lib/libopus.dylib" if os.uname().sysname == "Darwin" else "/usr/lib/aarch64-linux-gnu/libopus.so.0"))

# Silence useless bug reports messages
# youtube_dl.utils.bug_reports_message = lambda: ""

@app_commands.guild_only
class Music(BruhCasinoCog):
    music = app_commands.Group(name="music", description="we do a little ytmp3")

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.voice_states = {}

    def get_voice_state(self, ctx: Interaction) -> VoiceState:
        state = self.voice_states.get(ctx.guild.id)
        if not state or not state.exists:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self) -> None:
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    async def interaction_check(self, ctx: Interaction) -> bool:
        if not ctx.guild:
            raise commands.NoPrivateMessage("errrm, you can\"t use that here")
        return True

    @music.command(name="join")
    async def _join(self, ctx: Interaction) -> None:
        """Joins a voice channel."""
        await self.ensure_voice_state(ctx)
        await self.join(ctx)
        await ctx.response.send_message("joined",delete_after=5)

    async def join(self, ctx: Interaction) -> None:
        voice_state: VoiceState = self.get_voice_state(ctx)

        destination: discord.VoiceChannel = ctx.user.voice.channel
        if voice_state.voice:
            await voice_state.voice.move_to(destination)
            return

        voice_state.voice = await destination.connect()

    @music.command(name="summon")
    async def _summon(self, ctx: Interaction, channel: discord.VoiceChannel = None):
        """Summons the bot to a voice channel.
        If no channel was specified, it joins your channel.
        """
        voice_state: VoiceState = self.get_voice_state(ctx)

        if not channel and not ctx.user.voice:
            raise VoiceError("You are neither connected to a voice channel nor specified a channel to join.")

        destination = channel or ctx.user.voice.channel
        if voice_state.voice:
            await voice_state.voice.move_to(destination)
            await ctx.response.send_message("joined", ephemeral=True)
            return

        voice_state.voice = await destination.connect()
        await ctx.response.send_message("joined", ephemeral=True)

    @music.command(name="leave")
    async def _leave(self, ctx: Interaction) -> None:
        """Clears the queue and leaves the voice channel."""
        voice_state: VoiceState = self.get_voice_state(ctx)

        if not voice_state.voice:
            await ctx.response.send_message("Not connected to any voice channel.")
            return

        await voice_state.stop()
        del self.voice_states[ctx.guild.id]
        await ctx.response.send_message("stopped",delete_after=5)

    @music.command(name="volume")
    @commands.check_any(commands.is_owner(), is_developer())
    async def _volume(self, ctx: Interaction, volume: int) -> None:
        """Sets the volume of the player."""
        voice_state: VoiceState = self.get_voice_state(ctx)

        if not voice_state.is_playing:
            await ctx.response.send_message("nothing is playing")
            return

        if 0 > volume > 100:
            await ctx.response.send_message("volume must be between 0 and 100")
            return

        voice_state.volume = volume / 100
        await ctx.response.send_message("volume set to {}%".format(volume))

    @music.command(name="playing")
    async def _now(self, ctx: Interaction) -> None:
        """Displays the currently playing song."""
        voice_state: VoiceState = self.get_voice_state(ctx)

        if not voice_state.current or not voice_state.voice.is_playing():
            await ctx.response.send_message("nothing is playing")
            return
        embed = voice_state.current.create_embed()
        await ctx.response.send_message(embed=embed)

    @music.command(name="pause")
    async def _pause(self, ctx: Interaction) -> None:
        """Pauses the currently playing song."""
        voice_state: VoiceState = self.get_voice_state(ctx)

        if voice_state.is_playing and voice_state.voice.is_playing():
            voice_state.pause()
            await ctx.response.send_message("paused",delete_after=5)
            #await ctx.message.add_reaction("⏯")

    @music.command(name="resume")
    async def _resume(self, ctx: Interaction) -> None:
        """Resumes a currently paused song."""
        voice_state: VoiceState = self.get_voice_state(ctx)

        if not voice_state.is_playing and voice_state.voice.is_paused():
            voice_state.resume()
            await ctx.response.send_message("resumed",delete_after=5)
            #await ctx.message.add_reaction("⏯")

    @music.command(name="stop")
    async def _stop(self, ctx: Interaction) -> None:
        """Stops playing song and clears the queue."""
        voice_state: VoiceState = self.get_voice_state(ctx)

        voice_state.songs.clear()

        if voice_state.is_playing:
            voice_state.voice.stop()
            await ctx.response.send_message("stopped",delete_after=5)
            #await ctx.message.add_reaction("⏹")

    @music.command(name="skip")
    async def _skip(self, ctx: Interaction) -> None:
        """skip the song"""
        voice_state: VoiceState = self.get_voice_state(ctx)

        if not voice_state.is_playing:
            await ctx.response.send_message("it\"s rather quiet")
            return

        await ctx.response.send_message("skipping...")
        voice_state.skip()
        # voter = ctx.message.author
        # if voter == ctx.voice_state.current.requester:
        #     #await ctx.message.add_reaction("⏭")
        #     ctx.response.send_message("skipping...")
        #     ctx.voice_state.skip()

        # elif voter.id not in ctx.voice_state.skip_votes:
        #     ctx.voice_state.skip_votes.add(voter.id)
        #     total_votes = len(ctx.voice_state.skip_votes)

        #     if total_votes >= 3:
        #         await ctx.message.add_reaction("⏭")
        #         ctx.voice_state.skip()
        #     else:
        #         await ctx.response.send_message("Skip vote added, currently at **{}/3**".format(total_votes))

        # else:
        #     await ctx.response.send_message("You have already voted to skip this song.")

    @music.command(name="queue")
    async def _queue(self, ctx: Interaction, page: int = 1) -> None:
        """Shows the player"s queue.
        You can optionally specify the page to show. Each page contains 10 elements.
        """
        voice_state: VoiceState = self.get_voice_state(ctx)

        if len(voice_state.songs) == 0:
            await ctx.response.send_message("nothing in the queue")
            return

        items_per_page: int = 10
        pages: int = math.ceil(len(voice_state.songs) / items_per_page)

        start: int = (page - 1) * items_per_page
        end: int = start + items_per_page

        queue: str = ""
        for i, song in enumerate(voice_state.songs[start:end], start=start):
            queue += "`{0}.` [**{1.source.title}**]({1.source.url})\n".format(i + 1, song)

        embed = (discord.Embed(description="**{} tracks:**\n\n{}".format(len(voice_state.songs), queue))
                 .set_footer(text="page {}/{}".format(page, pages)))
        await ctx.response.send_message(embed=embed)

    @music.command(name="shuffle")
    async def _shuffle(self, ctx: Interaction) -> None:
        """Shuffles the queue."""
        voice_state: VoiceState = self.get_voice_state(ctx)

        if len(voice_state.songs) == 0:
            await ctx.response.send_message("nothing in the queue")
            return

        voice_state.songs.shuffle()
        await ctx.response.send_message("shuffled",delete_after=5)
        #await ctx.message.add_reaction("✅")

    @music.command(name="remove")
    async def _remove(self, ctx: Interaction, index: int) -> None:
        """Removes a song from the queue at a given index."""
        voice_state: VoiceState = self.get_voice_state(ctx)

        if len(voice_state.songs) == 0:
            await ctx.response.send_message("nothing in the queue")
            return

        voice_state.songs.remove(index - 1)
        await ctx.response.send_message("removed",delete_after=5)

    @_remove.autocomplete("index")
    async def remove_autocomplete(self, ctx: Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
        data = []
        for i, song in enumerate(self.voice_states.get(ctx.guild.id).songs, start=1):
            if current.lower() in (name := f"({i}) {song.source.title}").lower():
                data.append(app_commands.Choice(name=name, value=i))
        return data

    @music.command(name="loop")
    async def _loop(self, ctx: Interaction) -> None:
        """toggles loop on currently playing song"""
        voice_state: VoiceState = self.get_voice_state(ctx)

        if not voice_state.is_playing:
            await ctx.response.send_message("nothing is playing")
            return

        # Inverse boolean value to loop and unloop.
        voice_state.loop = not voice_state.loop
        #await ctx.message.add_reaction("✅")
        await ctx.response.send_message("Looping is now turned " + ("on" if voice_state.loop else "off"))

    # @app_commands.command(name="autoplay")
    # async def _autoplay(self, ctx: Interaction) -> None:
    #     """Automatically queue a new song that is related to the song at the end of the queue.
    #     Invoke this command again to toggle autoplay the song.
    #     """
    #
    #     if not ctx.voice_state.is_playing:
    #         await ctx.response.send_message("nothing is playing")
    #         return
    #
    #     # Inverse boolean value to loop and unloop.
    #     ctx.voice_state.autoplay = not ctx.voice_state.autoplay
    #     await ctx.response.send_message("Autoplay is now " + ("on" if ctx.voice_state.autoplay else "off"))

    @music.command(name="play")
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    async def _play(self, ctx: Interaction, search: str) -> None:
        """Plays a song.
        If there are songs in the queue, this will be queued until the
        other songs finished playing.
        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
        """
        await self.ensure_voice_state(ctx)
        voice_state: VoiceState = self.get_voice_state(ctx)
        await ctx.response.defer()
        source: typing.Union[YTDLSource, list[YTDLSource]] = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
        if not voice_state.voice:
            await self.join(ctx)
        
        is_playing: bool = voice_state.voice.is_playing()
        was_playing: bool = voice_state.current is not None
        if type(source) is list:
            for i in source:
                song: Song = Song(i)
                await voice_state.songs.put(song)

            await asyncio.sleep(1)
            await ctx.followup.send(content=f"queued {len(source)} songs")
            return

        song = Song(source)
        await voice_state.songs.put(song)

        if is_playing:
            await ctx.followup.send(f"queued [{str(source)}]({source.url})")
        elif not was_playing:
            await ctx.followup.send(embed=song.create_embed())

    @staticmethod
    async def ensure_voice_state(ctx: Interaction) -> None:
        voice_client: typing.Optional[VoiceProtocol] = ctx.guild.voice_client
        if (not ctx.user.voice or not ctx.user.voice.channel) and not voice_client:
            raise VoiceError("connect to a voice channel first")

        if voice_client:
            if voice_client.channel != ctx.user.voice.channel:
                raise VoiceError("i\'m already in a voice channel")


setup = Music.setup
