import discord
from discord.ext import commands
import os


client = commands.Bot(command_prefix='.')

@client.event
async def on_guild_join(guild):
    print(str(guild.id))


@client.event
async def on_ready():

    for filename in os.listdir("./cogs"):  # loads all cogs
        if filename.endswith(".py"):
            client.load_extension(f"cogs.{filename[:-3]}")

    await client.change_presence(status=discord.Status.online, activity=discord.Game("ur pls invite me"))
    print('client ready')

client.run(TOKEN)