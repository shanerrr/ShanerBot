import discord
from discord.ext import commands
import os
from discord.utils import get
import asyncio


client = commands.Bot(command_prefix=commands.when_mentioned_or('.'),description="ShaneBot is too cool for any discord server.")

@client.event
async def on_guild_join(guild):
    print(str(guild.id))


@client.event
async def on_ready():

    for filename in os.listdir("./cogs"):  # loads all cogs
        if filename.endswith(".py"):
            client.load_extension(f"cogs.{filename[:-3]}")

    await client.change_presence(status=discord.Status.online, activity=discord.Activity(name="ur pls invite me", type=discord.ActivityType.listening))
    print('client ready')

# async def disconnectTimer():
#
#     voice = get(client.voice_clients, guild=client.guild)
#     while not voice.is_playing() and voice:
#         await asyncio.sleep(3)
#         client.loop.create_task(disconnectTimer())
#
# client.loop.create_task(disconnectTimer())
client.run("")