import discord
from discord.ext import commands
import random


class Messaging(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.client.remove_command('help')

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                embed = discord.Embed(title="**ShanerBot** - The best Discord bot", description="👋 omg thanks for inviting me to your discord server.\nIt really means a lot.\n\nTyping **ur help** will provide all current available commands.", colour=discord.Color.dark_magenta())
                embed.set_thumbnail(url=self.client.user.avatar_url)
                await channel.send(embed=embed)
            break

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.content != "SHANER" and message.content.capitalize() == "Shaner":
            await message.channel.send("``what do you want man``")
        if message.content.find("SHANER") != -1:
            await message.channel.send("``MAN WHAT DO U WANT?``")
        if message.content.upper() == "KISS":
            suslist = ["i want you to interlock lips with me", "omg kiss me omg", "pls kiss me man", "ur have succulent lips man", "no ty, fgt stay in ur lane", "why r u so hot", "no thanks man", "not in the mood right now"]
            susit = random.randint(0, 7)
            await message.channel.send("``"+suslist[susit]+"``")
        if message.content.upper() == "HEY SHANER":
            if str(message.author.id) == "168603442175148032":
                await message.channel.send("``omg, yes master?``")

            elif str(message.author.id) == "234743458961555459":
                await message.channel.send("``hey daddy jerry``")
            else:
                mesgaut = (str(message.author)).split("#")
                print(str(message.author.id))
                await message.channel.send(f"``ok hey, **{mesgaut[0]}**``")

    @commands.command(pass_context=True)
    async def help(self, ctx):

        embed = discord.Embed(title="**ShanerBot - Commands List**", colour=discord.Color.dark_magenta())
        embed.set_footer(text=str(self.client.user.name), icon_url=self.client.user.avatar_url)
        embed.add_field(name="**- ur join**", value="ShanerBot will join the channel you're currently in. How nice!", inline=False)
        embed.add_field(name="**- ur leave**", value="ShanerBot will kindly leave the voice channel it is currently in.", inline=False)
        embed.add_field(name="**- ur play (url/query)**", value="ShanerBot will only look for one song. Put in a url or a very specific search query.", inline=False)
        embed.add_field(name="**- ur search (query)**", value="ShanerBot will search YouTube, returning 10 searches allowing you to choose what song to play or add to queue.", inline=False)
        embed.add_field(name="**- ur pause**", value="ShanerBot will pause any playing music.", inline=False)
        embed.add_field(name="**- ur stop**", value="ShanerBot will delete all songs in queue and stop playing any music.", inline=False)
        embed.add_field(name="**- ur skip**", value="ShanerBot will kindly skip any song for you. What a sweetheart.", inline=False)
        embed.add_field(name="**- ur volume (1-100)**", value="ShanerBot will reduce his volume by 1-100%", inline=False)
        embed.add_field(name="**- ur queue**", value="ShanerBot will return all the songs in the current queue.", inline=False)
        embed.add_field(name="**- ur repeat (one/off)**", value="ShanerBot will repeat one song, or all songs in current queue.", inline=False)
        embed.add_field(name="**- ur remove (position in queue)**", value=" ShanerBot will remove a song from queue.", inline=False)
        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(Messaging(client))
