import discord
from discord.ext import commands
import asyncio
from async_timeout import timeout
import os
import sys
import psutil
import logging


class Bot(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.msg = "ur help"

    @commands.command(pass_context=True)
    async def changemsg(self, ctx, *status: str):
        if str(ctx.author.id) == "168603442175148032" or str(ctx.author.id) == "234743458961555459":
            status = " ".join(status)
            self.msg = status
            await self.client.change_presence(status=discord.Status.online, activity=discord.Activity(name=f"{status}", type=discord.ActivityType.listening))
        else:
            await ctx.send("``nty, i don't like you.``")

    @commands.command(pass_context=True)
    async def changestatus(self, ctx, status: int):
        if str(ctx.author.id) == "168603442175148032" or str(ctx.author.id) == "234743458961555459":
            if status == 0: #offline
                await self.client.change_presence(status=discord.Status.offline, activity=discord.Activity(name=self.msg, type=discord.ActivityType.listening))
            elif status == 1: #online
                await self.client.change_presence(status=discord.Status.online, activity=discord.Activity(name=self.msg, type=discord.ActivityType.listening))
            elif status == 2: #do not disturb
                await self.client.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(name=self.msg, type=discord.ActivityType.listening))
            elif status == 3: #idle
                await self.client.change_presence(status=discord.Status.idle, activity=discord.Activity(name=self.msg, type=discord.ActivityType.listening))
            else:
                await ctx.send("``Invalid Status Code``")
        else:
            await ctx.send("``nty, i don't like you.``")

    @commands.command(pass_context=True)# work in progress
    async def reboot(self, ctx):
        if str(ctx.author.id) == "168603442175148032" or str(ctx.author.id) == "234743458961555459":
            check = await ctx.send("``Are you sure you want me to reboot?``")
            try:
                async with timeout(10):
                    while True:
                        msg = await self.client.wait_for('message', check=lambda
                            message: message.author == ctx.author and message.channel == ctx.channel)
                        try:
                            if msg.content.upper() == "NO":
                                break
                            elif msg.content.upper() == "YES":
                                break
                            else:
                                raise ValueError
                        except ValueError:
                            continue
            except asyncio.TimeoutError:
                await check.delete()
                await ctx.send("❌" + " ``Reboot not successful.``")
                return
            if msg.content.upper() == "NO":
                await check.delete()
                await ctx.send("❌" + " ``Reboot canceled.``")
                return
            else:
                await check.delete()
                await ctx.send("✔" + " ``Rebooting...``")
                try:
                    p = psutil.Process(os.getpid())
                    for handler in p.open_files() + p.connections():
                        os.close(handler.fd)
                except Exception as e:
                    logging.error(e)

                python = sys.executable
                os.execl(python, python, *sys.argv)


def setup(client):
    client.add_cog(Bot(client))

