import discord
from discord.ext import commands
from discord.utils import get
import youtube_dl
import datetime
from apiclient.discovery import build
import asyncio
import html
from async_timeout import timeout
from collections import defaultdict

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}
ffmpeg_options = {
    'before_options': '-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -threads 1'
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class AudioTooLongError(commands.CommandError):

    def __init__(self, client):
        self.client = client
        pass

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.25):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.imageurl = data.get('thumbnail')
        self.uploader = data.get('uploader')
        self.duration = data.get('duration')
        self.id = data.get('id')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        if data['duration'] > 3600:
            raise AudioTooLongError

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Music(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.ytapi = "API"
        self.repeatO = False
        self.repeatAll = False
        # self.repeatAllNum = 0
        # self.restart = False
        self.youtube = build('youtube', 'v3', developerKey=self.ytapi)
        self.active = False #so people can't do many different seraches if they havent answerd the first one
        self.players = defaultdict(list)

    @commands.command(pass_context=True)
    async def join(self, ctx):
        """- ShanerBot will join the channel you're currently in. How nice!"""

        try:
            channel = ctx.message.author.voice.channel
            voice = get(self.client.voice_clients, guild=ctx.guild)
        except AttributeError:
            await ctx.send("`ur know i cant join if ur're not in channel, right?`")
            return

        if voice is not None:
            await voice.move_to(channel)
            self.client.loop.create_task(self.disconnectTimer(ctx))
            return
        await channel.connect()
        self.client.loop.create_task(self.disconnectTimer(ctx))
        await ctx.send(f"`ok man, i joined: {channel}.`")

        print(ctx.guild.id)

    @commands.command(pass_context=True)
    async def leave(self, ctx):
        """- ShanerBot will kindly leave the voice channel it is currently in. """

        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            self.players[ctx.guild.id].clear()
            await voice.disconnect()
            await ctx.send(f"`ok, i left: {voice.channel}.`")
        else:
            await ctx.send("`man ur know im not connected to a channel, idot.`")

    @commands.command(pass_context=True)
    async def pause(self, ctx):
        """- ShanerBot will pause the current music playing. """

        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_playing():
            voice.pause()
            await ctx.send("`ok, paused.`")
        else:
            await ctx.send("`no music playing so ill just pause myself.`")

    @commands.command(pass_context=True)
    async def resume(self, ctx):
        """- ShanerBot will resume any paused music. """

        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_paused():
            voice.resume()
            await ctx.send("`ok i resume, ur welcome.`")
        else:
            await ctx.send("`ok ill resume nothing, idot.`")

    @commands.command(pass_context=True)
    async def stop(self, ctx):
        """- ShanerBot will destroy all songs in queue and stop playing any music. """

        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_playing():
            self.players[ctx.guild.id].clear()
            voice.stop()
            await ctx.send("`ok i stopped ur songs`")
        else:
            await ctx.send("`no song to stop. if only i can stop you from being an idot`")

    @commands.command(pass_context=True, aliases=['p'])
    async def play(self, ctx, *url: str):
        """- ShanerBot will only look for one song. Put in a url or a very specific search query. """

        if len(url) < 1:
            await ctx.send("``play what song man? enter youtube url or search.``")
            return

        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice is None:
            return

        searchlist = []
        urllist = []

        if self.players[ctx.guild.id]:

            if "&t=" in url[0] or "&list=" in url[0]:
                await ctx.send("**``🔎YouTube: "+url[0]+"``**")
                player = await YTDLSource.from_url(url[0], loop=self.client.loop, stream=True)
            else:
                song_search = " ".join(url)
                await ctx.send("**``🔎YouTube: " + song_search + "``**")

                req = self.youtube.search().list(q=song_search, part='snippet', type='video', maxResults=1)
                searchres = req.execute()
                for items in searchres['items']:
                    searchlist.append(items['snippet']['title'])
                    urllist.append(items['id']['videoId'])

                player = None
                try: #just if invalid url
                    player = await YTDLSource.from_url(f"https://www.youtube.com/watch?v={urllist[0]}",
                                                       loop=self.client.loop, stream=True)
                except IndexError:
                    await ctx.send("``omg man, i can't play that video. im so sorry 😔``")
                    return

            async with ctx.typing():
                self.players[ctx.guild.id].insert(0, player)
                embed = discord.Embed(title="**" + player.title + "**", colour=discord.Color.dark_magenta(), url=f"https://www.youtube.com/watch?v={player.id}")
                embed.set_author(name=str(ctx.author.name) + ": Adding a song",
                                 icon_url=ctx.author.avatar_url)  # client.user.avatar_url)
                embed.set_thumbnail(url=player.imageurl)
                embed.add_field(name="Duration", value=str(datetime.timedelta(seconds=round(player.duration))))
                embed.add_field(name="Position in queue", value=str(len(self.players[ctx.guild.id]) - 1))
                embed.add_field(name="Uploader", value=player.uploader)
                await ctx.send(embed=embed)


        elif not self.players[ctx.guild.id]:

            def check_queue():
                if self.players[ctx.guild.id]:
                    voice = get(self.client.voice_clients, guild=ctx.guild)
                    if self.repeatO:
                        voice.play(self.players[ctx.guild.id][-1], after=lambda e: check_queue())
                    elif self.repeatAll:
                        voice.source = discord.PCMVolumeTransformer(voice.source)
                        voice.source.volume = 0.25
                    else:
                        self.players[ctx.guild.id].pop()
                        player = self.players[ctx.guild.id][-1]
                        voice.play(player, after=lambda e: check_queue())
                else:
                    self.players[ctx.guild.id].clear()

            if "&t=" in url[0] or "&list=" in url[0]:
                await ctx.send("**``🔎YouTube: "+url[0]+"``**")
                player = await YTDLSource.from_url(url[0], loop=self.client.loop, stream=True)
            else:
                song_search = " ".join(url)
                await ctx.send("**``🔎YouTube: " + song_search + "``**")

                req = self.youtube.search().list(q=song_search, part='snippet', type='video', maxResults=1)
                searchres = req.execute()
                for items in searchres['items']:
                    searchlist.append(items['snippet']['title'])
                    urllist.append(items['id']['videoId'])

                player = None #just to init player var
                try: #for if nothing is found
                    player = await YTDLSource.from_url(
                        f"https://www.youtube.com/watch?v={urllist[0]}", loop=self.client.loop,
                        stream=True)
                except IndexError:
                    await ctx.send("``omg man, i can't play that video. im so sorry 😔``")
                    return

            async with ctx.typing():
                self.players[ctx.guild.id].insert(0, player)
                embed = discord.Embed(title="**" + player.title + "**", colour=discord.Color.dark_magenta(),
                                      url=f"https://www.youtube.com/watch?v={player.id}")
                embed.set_author(name=str(ctx.author.name) + ": Now Playing",
                                 icon_url=ctx.author.avatar_url)  # client.user.avatar_url)
                embed.set_thumbnail(url=player.imageurl)
                embed.add_field(name="Duration", value=str(datetime.timedelta(seconds=round(player.duration))))
                embed.add_field(name="Uploader", value=player.uploader)
                ctx.voice_client.play(player, after=lambda e: check_queue())
                await ctx.send(embed=embed)

        for emotion in url:
            if "SAD" in emotion.upper():
                await ctx.send("``hey man ur good? don't worry man im here for ur.``")
            if "HAPPY" in emotion.upper():
                await ctx.send("``omg ur happy? me 2 man.``")

    @commands.command(pass_context=True, aliases=['next'])
    async def skip(self, ctx):
        """- ShanerBot will kindly skip any song for you. What a sweetheart."""
        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_playing():
            if self.repeatAll: #for when queue is on repeat all
                songskip = (self.queues[self.repeatAllNum]).split("`|`")
                embed = discord.Embed(title="**" + songskip[0] + "**", colour=discord.Color.dark_magenta(),
                                      url=songskip[3])
                embed.set_author(name=str(ctx.author.name) + ": Skipped a song",
                                 icon_url=ctx.author.avatar_url)  # client.user.avatar_url)
                embed.set_thumbnail(url=songskip[3])
                await ctx.send(embed=embed)
                voice.stop() #stops song and starts next song if there is any song queued
            else:
                async with ctx.typing():
                    songskip = (self.players[ctx.guild.id][-1])
                    embed = discord.Embed(title="**" + songskip.title + "**", colour=discord.Color.dark_magenta(),
                                          url=f"https://www.youtube.com/watch?v={songskip.id}")
                    embed.set_author(name=str(ctx.author.name) + ": Skipped a song",
                                     icon_url=ctx.author.avatar_url)  # client.user.avatar_url)
                    embed.set_thumbnail(url=songskip.imageurl)
                    await ctx.send(embed=embed)
                    voice.stop()  # stops song and starts next song if there is any song queued

        else:
            await ctx.send("`no song to skip??????????`")

    @commands.command(pass_context=True, aliases=['vol'])
    async def volume(self, ctx, volume: int):
        """- If ShanerBot is too loud, you can reduce him by 1-100%"""

        if volume is None:
            return await ctx.send("`hey man, u need to put a number in, u know, to change the volume, idot.`")
        if ctx.voice_client is None:
            return await ctx.send("`hey man, cant really change volume if im not in a channel hahaha idot.`")
        if ctx.voice_client.source is None:
            return await ctx.send("`yeah man, ill changed the volume of this imaginary song, k did it.`")
        if volume > 100:
            return await ctx.send("`ur must be a different kind of stupid, ur want more than 100%? idot pls ur idot.`")
        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"`ur got it, volume is now at {volume}%`")

    @commands.command(pass_context=True, aliases=['q'])
    async def queue(self, ctx):
        """- ShanerBot returns all the songs in queue. """

        if len(self.players[ctx.guild.id]) == 0:
            await ctx.send("`bruh, nothing in queue.`")
            return
        if len(self.players[ctx.guild.id]) == 1:
            embed = discord.Embed(title="**"+(self.players[ctx.guild.id][-1]).title+"**", description="**Playing Now**",
                                  url=f"https://www.youtube.com/watch?v={(self.players[ctx.guild.id][-1]).id}",
                                  colour=discord.Color.dark_magenta())
            embed.set_thumbnail(url=(self.players[ctx.guild.id][-1]).imageurl)
            embed.set_footer(text=str(self.client.user.name), icon_url=self.client.user.avatar_url)
            await ctx.send(embed=embed)
        else:
            pos = 1
            length = len(self.players[ctx.guild.id])-1
            embed = discord.Embed(title="**"+(self.players[ctx.guild.id][length]).title+"**", url=f"https://www.youtube.com/watch?v={(self.players[ctx.guild.id][length]).id}", description="**Playing Now**",
                                  colour=discord.Color.dark_magenta())
            embed.set_thumbnail(url=(self.players[ctx.guild.id][length]).imageurl)
            embed.set_footer(text=str(self.client.user.name), icon_url=self.client.user.avatar_url)
            embed.add_field(name="-------------------------------------------------------------------------", value="**Currently In Queue:**")
            for num in range(length):
                item = self.players[ctx.guild.id][(length-1)-num]
                embed.add_field(name="**["+str(pos)+"] "+item.title+"**", value="https://www.youtube.com/watch?v=" +
                                                                                item.id, inline=False)
                pos += 1
            await ctx.send(embed=embed)

    # @commands.command(pass_context=True, aliases=['r'])
    # async def repeat(self, ctx, *repeat: str):
    #     """- ShanerBot can repeat one song, or all songs in current queue."""
    #     try:
    #         if "one".upper() in (x.upper() for x in repeat):
    #             if len(self.players[ctx.guild.id]) == 0:
    #                 await ctx.send("``No songs queued idot.``")
    #                 return
    #             self.repeatO = True
    #             length = len(self.players[ctx.guild.id]) - 1
    #             embed = discord.Embed(title="**"+self.players[ctx.guild.id][length].title+"**", description=f"**Repeating ({str(datetime.timedelta(seconds=round(self.players[ctx.guild.id][length].duration)))})**",
    #                                   url=f"https://www.youtube.com/watch?v={self.players[ctx.guild.id][length].id}",
    #                                   colour=discord.Color.dark_magenta())
    #             embed.set_thumbnail(url=self.players[ctx.guild.id][length].imageurl)
    #             await ctx.send(embed=embed)
    #         elif "all".upper() in (x.upper() for x in repeat):
    #             if len(self.players[ctx.guild.id]) == 0:
    #                 await ctx.send("``No songs queued idot.``")
    #                 return
    #             self.repeatAll = True
    #             self.repeatAllNum = len(self.queues)-1 #still have to work on
    #         elif "off".upper() in (x.upper() for x in repeat) and (self.repeatO or self.repeatAll):
    #             await ctx.send("``Repeating off``")
    #             self.repeatO = False
    #             self.repeatAll = False
    #         elif "off".upper() in (x.upper() for x in repeat):
    #             await ctx.send("``No songs queued idot.``")
    #
    #     except IndexError:
    #         await ctx.send("``Usage: ur repeat``**``(One/All/Off)``**")

    @commands.command(pass_context=True)
    async def search(self, ctx, *query: str):
        """- ShanerBot will search youtube, returning 10 searches allowing you to choose what song to play or add to queue."""

        if self.active:
            await ctx.send("🛑"+" ``bro, i'm busy right now. Reply to the active search man.``")
            return

        if len(query) < 1:
            await ctx.send("``search what song man?``")
            return

        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice is None:
            return

        def check_queue():

            if self.players[ctx.guild.id]:
                voice = get(self.client.voice_clients, guild=ctx.guild)
                if self.repeatO:
                    print(self.players[ctx.guild.id][-1].title)
                    voice.play(discord.FFmpegPCMAudio(self.players[ctx.guild.id][-1].url, **ffmpeg_options), after=lambda e: check_queue())
                elif self.repeatAll:
                    self.repeatAllNum -= 1

                    voice.source = discord.PCMVolumeTransformer(voice.source)
                    voice.source.volume = 0.25
                else:
                    self.players[ctx.guild.id].pop()
                    player = self.players[ctx.guild.id][-1]
                    voice.play(player, after=lambda e: check_queue())
            else:
                self.players[ctx.guild.id].clear()

        if not self.players[ctx.guild.id]: #for no songs in queue

            song_search = " ".join(query)
            if "www.youtube.com/watch?v=" in song_search:
                try:
                    player = await YTDLSource.from_url(song_search, loop=self.client.loop, stream=True)
                    self.players[ctx.guild.id].insert(0, player)
                    embed = discord.Embed(title="**" + player.title + "**", colour=discord.Color.dark_magenta(),
                                          url=f"https://www.youtube.com/watch?v={player.id}")
                    embed.set_author(name=str(ctx.author.name) + ": Now Playing",
                                     icon_url=ctx.author.avatar_url)  # client.user.avatar_url)
                    embed.set_thumbnail(url=player.imageurl)
                    embed.add_field(name="Duration", value=str(datetime.timedelta(seconds=round(player.duration))))
                    embed.add_field(name="Uploader", value=player.uploader)
                    await ctx.send(embed=embed)
                    ctx.voice_client.play(player, after=lambda e: check_queue())
                    return
                except youtube_dl.DownloadError:
                    await ctx.send("``omg man, i can't play that song. im so sorry 😔``")
                    return

            searchlist = []
            urllist = []

            req = self.youtube.search().list(q=song_search, part='snippet', type='video', maxResults=10)
            searchres = req.execute()
            if len(searchres['items']) != 0:
                for items in searchres['items']:
                    searchlist.append(html.unescape(items['snippet']['title']))
                    urllist.append(items['id']['videoId'])
            else:
                req = self.youtube.search().list(q="video|"+song_search, part='snippet', type='video', maxResults=10) #ensures we always get 10 results but videos  may be more general now
                searchres = req.execute()
                for items in searchres['items']:
                    searchlist.append(html.unescape(items['snippet']['title']))
                    urllist.append(items['id']['videoId'])

            embed = discord.Embed(title="**Search Results:**", description="**[1]:** "+searchlist[0]
                                                                          +"\n**[2]:** "+searchlist[1]
                                                                          +"\n**[3]:** "+searchlist[2]
                                                                          +"\n**[4]:** "+searchlist[3]
                                                                          +"\n**[5]:** "+searchlist[4]
                                                                          +"\n**[6]:** "+searchlist[5]
                                                                          +"\n**[7]:** "+searchlist[6]
                                                                          +"\n**[8]:** "+searchlist[7]
                                                                          +"\n**[9]:** "+searchlist[8]
                                                                          +"\n**[10]:** "+searchlist[9],
                                  colour=discord.Color.dark_magenta())
            embed.set_author(name=str(ctx.author.name)+": Picking a song", icon_url=ctx.author.avatar_url)  # client.user.avatar_url)
            embed.add_field(name="type 'cancel' to cancel request", value="**Select a number (1-10):**")
            search = await ctx.send(embed=embed)
            self.active = True
            try:
                async with timeout(20):
                    while True:
                        msg = await self.client.wait_for('message', check=lambda message: message.author == ctx.author and message.channel == ctx.channel)
                        try:
                            if msg.content.upper() == "CANCEL" or ".UR SEARCH" in msg.content.upper():
                                break
                            elif int(msg.content) in range(1, 11):
                                break
                            else:
                                raise ValueError
                        except ValueError:
                            continue
            except asyncio.TimeoutError:
                self.active = False
                await search.delete()
                await ctx.send("❌"+" ``man, you didn't choose a song in time.``")
                return
            if msg.content.upper() == "CANCEL" or ".UR SEARCH" in msg.content.upper():
                msg = None
                await search.delete()
                await ctx.send("❌" + " ``ok canceled.``")
                self.active = False
                return
            async with ctx.typing():
                player = await YTDLSource.from_url(f"https://www.youtube.com/watch?v={urllist[int(msg.content)-1]}", loop=self.client.loop, stream=True)
                print("dsadsadsadsad"+player)
                self.players[ctx.guild.id].insert(0, player)
                embed = discord.Embed(title="**"+player.title+"**", colour=discord.Color.dark_magenta(), url=f"https://www.youtube.com/watch?v={player.id}")
                embed.set_author(name=str(ctx.author.name) + ": Now Playing", icon_url=ctx.author.avatar_url)#client.user.avatar_url)
                embed.set_thumbnail(url=player.imageurl)
                embed.add_field(name="Duration", value=str(datetime.timedelta(seconds=round(player.duration))))
                embed.add_field(name="Uploader", value=player.uploader)
                await search.delete()
                await ctx.send(embed=embed)
                ctx.voice_client.play(player, after=lambda e: check_queue())
            self.active = False

        elif self.players[ctx.guild.id]:

            song_search = " ".join(query)
            if "www.youtube.com/watch?v=" in song_search:
                try:
                    player = await YTDLSource.from_url(song_search, loop=self.client.loop, stream=True)
                    self.players[ctx.guild.id].insert(0, player)
                    embed = discord.Embed(title="**" + player.title + "**", colour=discord.Color.dark_magenta(),
                                          url=f"https://www.youtube.com/watch?v={player.id}")
                    embed.set_author(name=str(ctx.author.name) + ": Adding a song", icon_url=ctx.author.avatar_url)
                    embed.set_thumbnail(url=player.imageurl)
                    embed.add_field(name="Duration", value=str(datetime.timedelta(seconds=round(player.duration))))
                    embed.add_field(name="Position in queue", value=str(len(self.players[ctx.guild.id]) - 1))
                    embed.add_field(name="Uploader", value=player.uploader)
                    await ctx.send(embed=embed)
                    return
                except youtube_dl.DownloadError:
                    await ctx.send("``omg man, i can't play that song. im so sorry 😔``")
                    return

            searchlist = [] #has all the results
            urllist = [] #for video id for player
            durlist = [] #has duration for all 10 results

            req = self.youtube.search().list(q=song_search, part='snippet', type='video', maxResults=10)
            searchres = req.execute()
            if len(searchres['items']) != 0:
                for items in searchres['items']:
                    searchlist.append(html.unescape(items['snippet']['title']))
                    urllist.append(items['id']['videoId'])
            else:
                req = self.youtube.search().list(q="video|"+song_search, part='snippet', type='video', maxResults=10) #ensures we always get 10 results but videos  may be more general now
                searchres = req.execute()
                for items in searchres['items']:
                    searchlist.append(html.unescape(items['snippet']['title']))
                    urllist.append(items['id']['videoId'])
                    durlist.append()

            embed = discord.Embed(title="**Search Results:**", description="**[1]:** "+searchlist[0]+f" **{durlist[0]}**"
                                                                           + "\n**[2]:** "+searchlist[1]
                                                                           + "\n**[3]:** "+searchlist[2]
                                                                           + "\n**[4]:** "+searchlist[3]
                                                                           + "\n**[5]:** "+searchlist[4]
                                                                           + "\n**[6]:** "+searchlist[5]
                                                                           + "\n**[7]:** "+searchlist[6]
                                                                           + "\n**[8]:** "+searchlist[7]
                                                                           + "\n**[9]:** "+searchlist[8]
                                                                           + "\n**[10]:** "+searchlist[9]
                                  , colour=discord.Color.dark_magenta())
            embed.set_author(name=str(ctx.author.name) + ": Picking a song",
                             icon_url=ctx.author.avatar_url)  # client.user.avatar_url)
            embed.add_field(name="type 'cancel' to cancel request", value="**Select a number (1-10):**")
            search = await ctx.send(embed=embed)
            self.active = True
            try:
                async with timeout(20):
                    while True:
                        msg = await self.client.wait_for('message', check=lambda
                            message: message.author == ctx.author and message.channel == ctx.channel)
                        try:
                            if msg.content.upper() == "CANCEL" or ".UR SEARCH" in msg.content.upper():
                                break
                            elif int(msg.content) in range(1, 11):
                                break
                            else:
                                raise ValueError
                        except ValueError:
                            continue
            except asyncio.TimeoutError:
                self.active = False
                await search.delete()
                await ctx.send("❌" + " ``man, you didn't choose a song in time.``")
                return
            if msg.content.upper() == "CANCEL" or ".UR SEARCH" in msg.content.upper():
                msg = None
                await search.delete()
                await ctx.send("❌" + " ``ok canceled.``")
                self.active = False
                return
            async with ctx.typing():
                player = await YTDLSource.from_url(
                    f"https://www.youtube.com/watch?v={urllist[int(msg.content) - 1]}", loop=self.client.loop,
                    stream=True)
                self.players[ctx.guild.id].insert(0, player)
                embed = discord.Embed(title="**"+player.title+"**", colour=discord.Color.dark_magenta(), url=f"https://www.youtube.com/watch?v={player.id}")
                embed.set_author(name=str(ctx.author.name) + ": Adding a song", icon_url=ctx.author.avatar_url)
                embed.set_thumbnail(url=player.imageurl)
                embed.add_field(name="Duration", value=str(datetime.timedelta(seconds=round(player.duration))))
                embed.add_field(name="Position in queue", value=str(len(self.players[ctx.guild.id])-1))
                embed.add_field(name="Uploader", value=player.uploader)
                await search.delete()
                await ctx.send(embed=embed)
            self.active = False

    @commands.command(pass_context=True)
    async def remove(self, ctx, *skip: int):
        """- ShanerBot will remove a song from queue."""
        if skip:
            voice = get(self.client.voice_clients, guild=ctx.guild)
            if voice and voice.is_playing():
                if 0 < skip[0] < len(self.players[ctx.guild.id]):
                    player = self.players[ctx.guild.id].pop(len(self.players[ctx.guild.id])-1-skip[0])
                    embed = discord.Embed(title="**" + player.title + "**", colour=discord.Color.dark_magenta(),
                                          url=f"https://www.youtube.com/watch?v={player.id}")
                    embed.set_author(name=str(ctx.author.name) + ": Removed a song", icon_url=ctx.author.avatar_url)
                    embed.set_thumbnail(url=player.imageurl)
                    embed.add_field(name="Duration", value=str(datetime.timedelta(seconds=round(player.duration))))
                    embed.add_field(name="Was in queue", value=str(skip[0]))
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("``yup, sure, let me remove this non-existent song.``")
            else:
                await ctx.send("``bruh, i need a song in the queue to remove it.``")
        else:
            await ctx.send("``remove what song?``")

    @play.before_invoke
    @search.before_invoke
    async def voice_connected(self, ctx):

        voice = get(self.client.voice_clients, guild=ctx.guild)
        try:
            channel = ctx.message.author.voice.channel
            if voice is not None:
                await voice.move_to(channel)
                self.client.loop.create_task(self.disconnectTimer(ctx))
                return
            else:
                await channel.connect()
                self.client.loop.create_task(self.disconnectTimer(ctx))
        except AttributeError:
            await ctx.send("``man where am i going to play it huh? join channel first idot.``")

    async def disconnectTimer(self, ctx): #ensures if bot is not in use, it'll leave
        await self.client.wait_until_ready()
        voice = get(self.client.voice_clients, guild=ctx.guild)
        await asyncio.sleep(1000)
        while voice.is_playing():
            await asyncio.sleep(1200)
        self.players[ctx.guild.id].clear()
        await voice.disconnect()


def setup(client):
    client.add_cog(Music(client))
