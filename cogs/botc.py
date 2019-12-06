import discord
from discord.ext import commands
from discord.utils import get
import youtube_dl
import os
from os import system
import shutil
import datetime

class Bot(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(pass_context=True)
    async def changemsg(self, ctx, *status: str):
        if str(ctx.author.id) == "168603442175148032":
            status = " ".join(status)
            await self.client.change_presence(status=discord.Status.online, activity=discord.Activity(name=f"{status}", type=discord.ActivityType.listening))
        else:
            await ctx.send("``nty, i don't like you.``")

    @commands.command(pass_context=True)
    async def changestatus(self, ctx, status: int):
        if str(ctx.author.id) == "168603442175148032":
            if status == 0: #offline
                await self.client.change_presence(status=discord.Status.offline, activity=discord.Activity(name="ur pls invite me", type=discord.ActivityType.listening))
            elif status == 1: #online
                await self.client.change_presence(status=discord.Status.online, activity=discord.Activity(name="ur pls invite me", type=discord.ActivityType.listening))
            elif status == 2: #do not disturb
                await self.client.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(name="ur pls invite me", type=discord.ActivityType.listening))
            elif status == 3: #idle
                await self.client.change_presence(status=discord.Status.idle, activity=discord.Activity(name="ur pls invite me", type=discord.ActivityType.listening))
            else:
                await ctx.send("``Invalid Status Code``")
        else:
            await ctx.send("``nty, i don't like you.``")


def setup(client):
    client.add_cog(Bot(client))

