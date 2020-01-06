import discord
from discord.ext import commands
from discord.utils import find
import asyncio
import random


class Messaging(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.client.remove_command('help')

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        general = find(lambda x: x.name == 'general', guild.text_channels)
        if general and general.permissions_for(guild.me).send_messages:
            embed = discord.Embed(title="**ShanerBot** - The best Discord bot",
                                  description="👋 omg thanks for inviting me to your discord server.\nIt really means a lot.\n\nTyping **ur help** will provide all current available commands.",
                                  colour=discord.Color.dark_magenta())
            embed.set_thumbnail(url=self.client.user.avatar_url)
            await general.send(embed=embed)
        else:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    embed = discord.Embed(title="**ShanerBot** - The best Discord bot", description="👋 omg thanks for inviting me to your discord server.\nIt really means a lot.\n\nTyping **ur help** will provide all current available commands.", colour=discord.Color.dark_magenta())
                    embed.set_thumbnail(url=self.client.user.avatar_url)
                    await channel.send(embed=embed)
                break

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.content.capitalize() == "Shaner":
            replylist = ["what do you want man.", "?", "im busy right now actually doing something.", "yeah?", "how can i be an assistance to you?", "nope, don't like you."]
            await message.channel.send("``"+replylist[random.randint(0, 5)]+"``")
        if message.content.upper() == "KISS":
            suslist = ["i want you to interlock lips with me", "omg kiss me omg", "pls kiss me man", "ur have succulent lips man", "no ty, fgt stay in ur lane", "why r u so hot", "no thanks man", "not in the mood right now"]
            await message.channel.send("``"+suslist[random.randint(0, 7)]+"``")
        if message.content.upper() == "HEY SHANER":
            if str(message.author.id) == "168603442175148032":
                await message.channel.send("``omg, yes master?``")
            elif str(message.author.id) == "234743458961555459":
                await message.channel.send("``hey daddy jerry.``")
            else:
                mesgaut = (str(message.author)).split("#")
                await message.channel.send(f"``ok hey, {mesgaut[0]}.``")
                return
            embed = discord.Embed(title="**ShanerBot** - Admin Panel",
                                      description="\n**- ur changemsg (message)** - Changes ShanerBot's activity message.\n**- ur changestatus (0-3)** - Changes ShanerBot's status.",
                                      colour=discord.Color.dark_magenta())
            embed.add_field(name="**         ur changestatus 0 - Appears Offline\n         ur changestatus 1 - Online\n         ur changestatus 2 - Do Not Disturb\n         ur changestatus 3 - Idle**",
                            value="**\n**", inline=False)
            await message.channel.send(embed=embed)

        if "assimilate" in message.content.lower():
            if message.author.voice.channel.permissions_for(message.author).administrator:
                chperms = message.author.voice.channel.permissions_for(message.guild.me)
                assim = ["oh look, another Shaner.", "oh, look a shaner.", "another one.", "weird, a shaner appeared."]
                if chperms.manage_nicknames:
                    await message.channel.send("😈" + " ``Hehehe.``")
                    await asyncio.sleep(2)
                    for member in message.author.voice.channel.members:
                        try:
                            await member.edit(nick="Shaner")
                            if random.randint(0, 1) == 1:
                                await message.channel.send("``"+assim[random.randint(0, 3)]+"``")
                        except discord.errors.Forbidden:
                            continue
                    await message.channel.send("``Hello all Shaners!``")
                else:
                    await message.channel.send("😧"+" ``I don't have the permissions to perform this activity.``")
            else:
                await message.channel.send("``lol, im not listening to you, idot.``")

        if "bye shaner" in message.content.lower():
            byelist = ["Take care sweetie.", "Adios.", "omg before you go, take this 😘", "see ya l8ter alig8ter.",
                       "Goodbyes are not forever, are not the end; it simply means I'll miss you until we meet again.",
                       "Never say goodbye because goodbye means going away and going away means forgetting.",
                       "Good friends never say goodbye. They simply say “See you soon."]
            if str(message.author.id) == "234743458961555459":
                await message.channel.send("``"+"Jer, "+byelist[random.randint(0, 6)]+"``")
                return
            if str(message.author.id) == "168603442175148032":
                await message.channel.send("``"+"Shan, "+byelist[random.randint(0, 6)]+"``")
                return
            await message.channel.send(f"``{byelist[random.randint(0, 6)]}``")

    @commands.command(pass_context=True)
    async def help(self, ctx):

        embed = discord.Embed(title="**ShanerBot - Commands List**", colour=discord.Color.dark_magenta())
        embed.set_footer(text=str(self.client.user.name), icon_url=self.client.user.avatar_url)
        embed.add_field(name="**- ur join**", value="ShanerBot will join the channel you're currently in. How nice!", inline=False)
        embed.add_field(name="**- ur leave**", value="ShanerBot will kindly leave the voice channel it is currently in.", inline=False)
        embed.add_field(name="**- ur play (url/query)**", value="ShanerBot will only look for one song. Put in a url or a very specific search query.", inline=False)
        embed.add_field(name="**- ur search (query)**", value="ShanerBot will search YouTube, returning 10 searches allowing you to choose what song to play or add to queue.", inline=False)
        embed.add_field(name="**- ur restart**", value=" ShanerBot will restart a playing song.", inline=False)
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
