import discord
import yt_dlp as youtube_dl
from discord.ext import commands
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Music-related variables
voice_clients = {}
song_queue = {}
yt_dl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'default_search': 'ytsearch',
}
ytdl = youtube_dl.YoutubeDL(yt_dl_opts)
ffmpeg_options = {'options': "-vn"}

async def play_next_song(bot, guild_id):
    if guild_id in song_queue and song_queue[guild_id]:
        song_url, song_title = song_queue[guild_id].pop(0)
        voice_client = voice_clients[guild_id]
        player = discord.FFmpegPCMAudio(song_url, **ffmpeg_options)
        voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(bot, guild_id), bot.loop).result())
        await bot.get_channel(voice_clients[guild_id].channel.id).send(f"Now playing: {song_title}")
    else:
        if guild_id in voice_clients:
            await voice_clients[guild_id].disconnect()
            del voice_clients[guild_id]
            del song_queue[guild_id]

def setup(bot):
    @bot.command(name='play')
    async def play(ctx, *, query):
        logger.info(f"!play is used by {ctx.author} in {ctx.guild}")
        if ctx.author.voice is None:
            await ctx.send("You are not connected to a voice channel.")
            return

        voice_channel = ctx.author.voice.channel
        if ctx.guild.id not in voice_clients or voice_clients[ctx.guild.id].channel != voice_channel:
            if ctx.guild.id in voice_clients:
                await voice_clients[ctx.guild.id].disconnect()
            voice_client = await voice_channel.connect()
            voice_clients[ctx.guild.id] = voice_client
        else:
            voice_client = voice_clients[ctx.guild.id]

        data = ytdl.extract_info(f"ytsearch:{query}", download=False)
        if 'entries' in data:
            video = data['entries'][0]
            song_url = video['url']
            song_title = video['title']

            if ctx.guild.id not in song_queue:
                song_queue[ctx.guild.id] = []
            song_queue[ctx.guild.id].append((song_url, song_title))

            await ctx.send(f"Added {song_title} to the queue.")
            if not voice_client.is_playing():
                await play_next_song(bot, ctx.guild.id)
        else:
            await ctx.send("No results found.")

    @bot.command(name='pause')
    async def pause(ctx):
        logger.info(f"!pause is used by {ctx.author} in {ctx.guild}")
        try:
            if ctx.guild.id in voice_clients and voice_clients[ctx.guild.id].is_playing():
                voice_clients[ctx.guild.id].pause()
                await ctx.send("Playback paused.")
            else:
                await ctx.send("No audio is currently playing.")
        except Exception as err:
            logger.error(f"Error: {err}")
            await ctx.send(f"An error occurred: {err}")

    @bot.command(name='resume')
    async def resume(ctx):
        logger.info(f"!resume is used by {ctx.author} in {ctx.guild}")
        try:
            if ctx.guild.id in voice_clients and voice_clients[ctx.guild.id].is_paused():
                voice_clients[ctx.guild.id].resume()
                await ctx.send("Playback resumed.")
            else:
                await ctx.send("Audio is not paused.")
        except Exception as err:
            logger.error(f"Error: {err}")
            await ctx.send(f"An error occurred: {err}")

    @bot.command(name='stop')
    async def stop(ctx):
        logger.info(f"!stop is used by {ctx.author} in {ctx.guild}")
        try:
            if ctx.guild.id in voice_clients:
                voice_clients[ctx.guild.id].stop()
                await voice_clients[ctx.guild.id].disconnect()
                del voice_clients[ctx.guild.id]
                del song_queue[ctx.guild.id]
                await ctx.send("Playback stopped and disconnected.")
            else:
                await ctx.send("Bot is not connected to a voice channel.")
        except Exception as err:
            logger.error(f"Error: {err}")
            await ctx.send(f"An error occurred: {err}")
