import discord
from discord.ext import commands
from discord.utils import get
import random
import youtube_dl
import os
from os import system
import shutil
import datetime


class Messaging(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.content != "SHANER" and message.content.capitalize() == "Shaner":
            await message.channel.send("what do you want man")
        if message.content.find("SHANER") != -1:
            await message.channel.send("MAN WHAT DO U WANT?")
        if message.content.upper() == "KISS":
            suslist = ["i want you to interlock lips with me", "omg kiss me omg", "pls kiss me man", "ur have succulent lips man", "no ty, fgt stay in ur lane"]
            susit = random.randint(0,3)
            await message.channel.send(suslist[susit])
        if message.content.upper() == "HEY SHANER":
            if str(message.author.id) == "168603442175148032":
                await message.channel.send("omg, yes master?")
            elif str(message.author.id) == "234743458961555459":
                await message.channel.send("hey daddy jerry")
            else:
                mesgaut = (str(message.author)).split("#")
                print(str(message.author.id))
                await message.channel.send(f"ok hey, **{mesgaut[0]}**")

        await self.client.process_commands(message)


def setup(client):
    client.add_cog(Messaging(client))