import discord
from discord.ext import commands
from discord.utils import get
import asyncio

class Voice(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):  # strictly joining and disconnecting.

        voice = get(self.client.voice_clients, guild=member.guild)
        if voice and not member.bot:
            if not voice.is_playing():
                if before.channel and not after.channel:
                    if before.channel == voice.channel:
                        voice.stop()
                        voice.play(discord.FFmpegPCMAudio("UserDC.mp3"))
                        voice.source = discord.PCMVolumeTransformer(voice.source)
                    voice.source.volume = 0.07
                elif after.channel and not before.channel:
                    if after.channel == voice.channel:
                        voice.stop()
                        voice.play(discord.FFmpegPCMAudio("UserJC.mp3"))
                        voice.source = discord.PCMVolumeTransformer(voice.source)
                        voice.source.volume = 0.07

def setup(client):
    client.add_cog(Voice(client))