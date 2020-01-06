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

youtube_dl.utils.bug_reports_message = lambda: ''
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
    pass
class LiveStreamError(commands.CommandError):
    pass
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.10):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.imageurl = data.get('thumbnail')
        self.uploader = data.get('uploader')
        self.duration = data.get('duration')
        self.id = data.get('id')

    @classmethod
    async def from_url(cls, ctx, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        if data['duration'] > 5400:
            await ctx.send("😠"+" ``Song too long man.``")
            raise AudioTooLongError
        elif data['duration'] == 0: #livestream check
            await ctx.send("``sorry dude, can't play livestreams.``")
            raise LiveStreamError

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Music(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.ytapi = "API"
        self.youtube = build('youtube', 'v3', developerKey=self.ytapi)

        self.volume = {}
        self.volume = defaultdict(lambda: 0.10, self.volume)

        self.repeatO = {}
        self.repeatO = defaultdict(lambda: False, self.repeatO)

        self.repeatAll = {}
        self.repeatAll = defaultdict(lambda: False, self.repeatAll)

        self.restart = {}
        self.restart = defaultdict(lambda: False, self.restart)

        self.active = {}
        self.active = defaultdict(lambda: False, self.active)# sets all new keys to false
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

        chperms = channel.permissions_for(ctx.guild.me)
        if not chperms.connect: #no channel perms
            await ctx.send("😢" + " ``mannnn, i don't have the permission to join that channel.``")
            return
        if channel.user_limit != 0 and (len(channel.members) >= channel.user_limit):
            if chperms.connect and (chperms.move_members or chperms.administrator):
                pass
            else:
                await ctx.send("😭" + " ``there is not enough room for me man, ttyl.``")
                return
        if voice is not None:
            await voice.move_to(channel)
            return
        await channel.connect()

        self.client.loop.create_task(self.disconnectTimer(ctx))
        await ctx.send(f"`ok man, i joined: {channel}.`")

    @commands.command(pass_context=True)
    async def leave(self, ctx):
        """- ShanerBot will kindly leave the voice channel it is currently in. """

        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            self.players[ctx.guild.id].clear()
            self.repeatO[ctx.guild.id] = False
            self.repeatAll[ctx.guild.id] = False
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

    @commands.command(pass_context=True, aliases=['clear'])
    async def stop(self, ctx):
        """- ShanerBot will destroy all songs in queue and stop playing any music. """

        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_playing():
            self.players[ctx.guild.id].clear()
            self.repeatO[ctx.guild.id] = False
            self.repeatAll[ctx.guild.id] = False
            voice.stop()
            await ctx.send("`ok i stopped ur songs.`")
        else:
            await ctx.send("`no song to stop. if only i can stop you from being an idot.`")

    @commands.command(pass_context=True, aliases=['p'])
    async def play(self, ctx, *url: str):
        """- ShanerBot will only look for one song. Put in a url or a very specific search query. """

        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice is None:
            return
        if not url:
            await ctx.send("``play what song man? enter youtube url or search.``")
            return
        if len(self.players[ctx.guild.id]) == 10:
            await ctx.send("``sorry man, i can't have more than 10 songs queued.``")
            return

        searchlist = []
        urllist = []

        if self.players[ctx.guild.id]:#items in queue

            if "&t=" in url[0] or "&list=" in url[0]:
                await ctx.send("**``🔎YouTube: "+url[0]+"``**")
                player = await YTDLSource.from_url(ctx, url[0], loop=self.client.loop, stream=True)
            else:
                song_search = " ".join(url)
                await ctx.send("**``🔎YouTube: " + song_search + "``**")

                req = self.youtube.search().list(q=song_search, part='snippet', type='video', maxResults=1)
                searchres = req.execute()
                for items in searchres['items']:
                    searchlist.append(items['snippet'])
                    urllist.append(items['id']['videoId'])
                if searchlist[0]['liveBroadcastContent'] == "live":
                    await ctx.send("``I can't play livestreams dude.``")
                    return

                try: #just if invalid url
                    player = await YTDLSource.from_url(ctx, f"https://www.youtube.com/watch?v={urllist[0]}",
                                                       loop=self.client.loop, stream=True)
                except IndexError:
                    await ctx.send("``omg man, i can't play that video. im so sorry 😔``")
                    return
                except AudioTooLongError:
                    return

            async with ctx.typing():
                self.players[ctx.guild.id].insert(0, player)
                embed = discord.Embed(title="**" + player.title + "**", colour=discord.Color.dark_magenta(), url=f"https://www.youtube.com/watch?v={player.id}")
                embed.set_author(name=str(ctx.author.name) + ": Adding a song",
                                 icon_url=ctx.author.avatar_url)
                embed.set_thumbnail(url=player.imageurl)
                embed.add_field(name="Duration", value=str(datetime.timedelta(seconds=round(player.duration))))
                embed.add_field(name="Position in queue", value=str(len(self.players[ctx.guild.id]) - 1))
                embed.add_field(name="Uploader", value=player.uploader)
            await ctx.send(embed=embed)

        elif not self.players[ctx.guild.id]:# no items in queue

            def check_queue():
                if self.players[ctx.guild.id]:
                    voice = get(self.client.voice_clients, guild=ctx.guild)
                    if self.restart[ctx.guild.id]:
                        voice.play(discord.FFmpegPCMAudio(self.players[ctx.guild.id][-1].url, **ffmpeg_options),
                                   after=lambda e: check_queue())
                        voice.source = discord.PCMVolumeTransformer(voice.source)
                        voice.source.volume = self.volume[ctx.guild.id]
                        self.restart[ctx.guild.id] = False
                    elif self.repeatO[ctx.guild.id]:
                        voice.play(discord.FFmpegPCMAudio(self.players[ctx.guild.id][-1].url, **ffmpeg_options),
                                   after=lambda e: check_queue())
                        voice.source = discord.PCMVolumeTransformer(voice.source)
                        voice.source.volume = self.volume[ctx.guild.id]
                    elif self.repeatAll[ctx.guild.id]:
                        if len(self.players[ctx.guild.id]) == 1:
                            voice.play(discord.FFmpegPCMAudio(self.players[ctx.guild.id][-1].url, **ffmpeg_options),
                                       after=lambda e: check_queue())
                        else:
                            songreinsert = self.players[ctx.guild.id].pop()
                            voice.play(self.players[ctx.guild.id][-1], after=lambda e: check_queue())
                            self.players[ctx.guild.id].insert(0, songreinsert)
                    else:
                        self.players[ctx.guild.id].pop()
                        player = self.players[ctx.guild.id][-1]
                        voice.play(player, after=lambda e: check_queue())
                else:
                    return

            if "&t=" in url[0] or "&list=" in url[0]:
                await ctx.send("**``🔎YouTube: "+url[0]+"``**")
                try:
                    player = await YTDLSource.from_url(ctx, url[0], loop=self.client.loop, stream=True)
                except AudioTooLongError:
                    return
            else:
                song_search = " ".join(url)
                await ctx.send("**``🔎YouTube: " + song_search + "``**")

                req = self.youtube.search().list(q=song_search, part='snippet', type='video', maxResults=1)
                searchres = req.execute()
                for items in searchres['items']:
                    searchlist.append(items['snippet'])
                    urllist.append(items['id']['videoId'])
                if searchlist[0]['liveBroadcastContent'] == "live":
                    await ctx.send("``I can't play livestreams dude.``")
                    return

                try: #for if nothing is found
                    player = await YTDLSource.from_url(ctx,
                        f"https://www.youtube.com/watch?v={urllist[0]}", loop=self.client.loop,
                        stream=True)
                except IndexError:
                    await ctx.send("``omg man, i can't play that video. im so sorry 😔``")
                    return
                except AudioTooLongError:
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
        self.repeatO[ctx.guild.id] = False
        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_playing():
            async with ctx.typing():
                songskip = (self.players[ctx.guild.id][-1])
                embed = discord.Embed(title="**" + songskip.title + "**", colour=discord.Color.dark_magenta(),
                                      url=f"https://www.youtube.com/watch?v={songskip.id}")
                embed.set_author(name=str(ctx.author.name) + ": Skipped a song",
                                 icon_url=ctx.author.avatar_url)  # client.user.avatar_url)
                embed.set_thumbnail(url=songskip.imageurl)
                voice.stop()  # stops song and starts next song if there is any song queued
            await ctx.send(embed=embed)
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
        self.volume[ctx.guild.id] = volume / 100
        await ctx.send(f"`🔊 ur got it, volume is now at {volume}%`")

    @commands.command(pass_context=True, aliases=['q', 'np'])
    async def queue(self, ctx):
        """- ShanerBot returns all the songs in queue. """

        if len(self.players[ctx.guild.id]) == 0:
            await ctx.send("`bruh, nothing in queue.`")
            return
        if len(self.players[ctx.guild.id]) == 1:
            if self.repeatO[ctx.guild.id]:
                embed = discord.Embed(title="**" + (self.players[ctx.guild.id][-1]).title + "**",
                                      description="**Playing Now (🔂)**",
                                      url=f"https://www.youtube.com/watch?v={(self.players[ctx.guild.id][-1]).id}",
                                      colour=discord.Color.dark_magenta())
                embed.set_thumbnail(url=(self.players[ctx.guild.id][-1]).imageurl)
                embed.set_footer(text=str(self.client.user.name), icon_url=self.client.user.avatar_url)
            elif self.repeatAll[ctx.guild.id]:
                embed = discord.Embed(title="**" + (self.players[ctx.guild.id][-1]).title + "**",
                                      description="**Playing Now (🔁)**",
                                      url=f"https://www.youtube.com/watch?v={(self.players[ctx.guild.id][-1]).id}",
                                      colour=discord.Color.dark_magenta())
                embed.set_thumbnail(url=(self.players[ctx.guild.id][-1]).imageurl)
                embed.set_footer(text=str(self.client.user.name), icon_url=self.client.user.avatar_url)
            else:
                embed = discord.Embed(title="**"+(self.players[ctx.guild.id][-1]).title+"**", description="**Playing Now**",
                                      url=f"https://www.youtube.com/watch?v={(self.players[ctx.guild.id][-1]).id}",
                                      colour=discord.Color.dark_magenta())
                embed.set_thumbnail(url=(self.players[ctx.guild.id][-1]).imageurl)
                embed.set_footer(text=str(self.client.user.name), icon_url=self.client.user.avatar_url)
            await ctx.send(embed=embed)
        else:
            pos = 1
            length = len(self.players[ctx.guild.id])-1
            if self.repeatO[ctx.guild.id]:
                embed = discord.Embed(title="**"+(self.players[ctx.guild.id][length]).title+"**", url=f"https://www.youtube.com/watch?v={(self.players[ctx.guild.id][length]).id}", description="**Playing Now (🔂)**",
                                      colour=discord.Color.dark_magenta())
            elif self.repeatAll[ctx.guild.id]:
                embed = discord.Embed(title="**" + (self.players[ctx.guild.id][-1]).title + "**",
                                      description="**Playing Now (🔁)**",
                                      url=f"https://www.youtube.com/watch?v={(self.players[ctx.guild.id][-1]).id}",
                                      colour=discord.Color.dark_magenta())
            else:
                embed = discord.Embed(title="**"+(self.players[ctx.guild.id][length]).title+"**", url=f"https://www.youtube.com/watch?v={(self.players[ctx.guild.id][length]).id}", description="**Playing Now**",
                                      colour=discord.Color.dark_magenta())
            embed.set_thumbnail(url=(self.players[ctx.guild.id][length]).imageurl)
            embed.set_footer(text=str(self.client.user.name), icon_url=self.client.user.avatar_url)
            embed.add_field(name="-------------------------------------------------------------------------", value="**Currently In Queue:**")
            for num in range(length):
                item = self.players[ctx.guild.id][(length-1)-num]
                embed.add_field(name="**["+str(pos)+"]: "+item.title+"**"+f" - [{str(datetime.timedelta(seconds=round(item.duration)))}]", value="https://www.youtube.com/watch?v=" +
                                                                                item.id, inline=False)
                pos += 1
            await ctx.send(embed=embed)

    @commands.command(pass_context=True, aliases=['r', 'loop'])
    async def repeat(self, ctx, *repeat: str):
        """- ShanerBot can repeat one song, or all songs in current queue."""
        if not repeat:
            await ctx.send("``what? repeat one or all songs? (one/all/off)``")
        else:
            if "one".upper() in (x.upper() for x in repeat):
                self.repeatAll[ctx.guild.id] = False
                if len(self.players[ctx.guild.id]) == 0:
                    await ctx.send("``No songs queued idot.``")
                    return
                self.repeatO[ctx.guild.id] = True
                length = len(self.players[ctx.guild.id]) - 1
                embed = discord.Embed(title="**"+self.players[ctx.guild.id][length].title+"**", description=f"**Repeating ({str(datetime.timedelta(seconds=round(self.players[ctx.guild.id][length].duration)))})**",
                                      url=f"https://www.youtube.com/watch?v={self.players[ctx.guild.id][length].id}",
                                      colour=discord.Color.dark_magenta())
                embed.set_thumbnail(url=self.players[ctx.guild.id][length].imageurl)
                embed.set_footer(text=str(self.client.user.name), icon_url=self.client.user.avatar_url)
                await ctx.send(embed=embed)
            elif "all".upper() in (x.upper() for x in repeat):
                self.repeatO[ctx.guild.id] = False
                if len(self.players[ctx.guild.id]) == 0:
                    await ctx.send("``No songs queued idot.``")
                    return
                self.repeatAll[ctx.guild.id] = True
                await ctx.send("🔁"+"`` Queue is repeating.``")
            elif "off".upper() in (x.upper() for x in repeat) and (self.repeatO or self.repeatAll):
                await ctx.send("``ok man repeating is off.``")
                self.repeatO[ctx.guild.id] = False
                self.repeatAll[ctx.guild.id] = False
            elif "off".upper() in (x.upper() for x in repeat):
                await ctx.send("``No songs queued idot.``")

    @commands.command(pass_context=True)
    async def search(self, ctx, *query: str):
        """- ShanerBot will search youtube, returning 10 searches allowing you to choose what song to play or add to queue."""

        if self.active[ctx.guild.id] is True:
            await ctx.send("🛑"+" ``bro, i'm busy right now. Reply to the active search man.``")
            return

        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice is None:
            return
        if not query:
            await ctx.send("``search what song man?``")
            return
        if len(self.players[ctx.guild.id]) == 10:
            await ctx.send("``sorry man, i can't have more than 10 songs queued.``")
            return

        def check_queue():
            if self.players[ctx.guild.id]:
                voice = get(self.client.voice_clients, guild=ctx.guild)
                if self.restart[ctx.guild.id]:
                    voice.play(discord.FFmpegPCMAudio(self.players[ctx.guild.id][-1].url, **ffmpeg_options),
                               after=lambda e: check_queue())
                    voice.source = discord.PCMVolumeTransformer(voice.source)
                    voice.source.volume = self.volume[ctx.guild.id]
                    self.restart[ctx.guild.id] = False
                elif self.repeatO[ctx.guild.id]:
                    voice.play(discord.FFmpegPCMAudio(self.players[ctx.guild.id][-1].url, **ffmpeg_options), after=lambda e: check_queue())
                    voice.source = discord.PCMVolumeTransformer(voice.source)
                    voice.source.volume = self.volume[ctx.guild.id]
                elif self.repeatAll[ctx.guild.id]:
                    if len(self.players[ctx.guild.id]) == 1:
                        voice.play(discord.FFmpegPCMAudio(self.players[ctx.guild.id][-1].url, **ffmpeg_options),
                                   after=lambda e: check_queue())
                        voice.source = discord.PCMVolumeTransformer(voice.source)
                        voice.source.volume = 0.10
                    else:
                        songreinsert = self.players[ctx.guild.id].pop()
                        self.players[ctx.guild.id].insert(0, songreinsert)
                        voice.play(discord.FFmpegPCMAudio(self.players[ctx.guild.id][-1].url, **ffmpeg_options),
                                   after=lambda e: check_queue())
                        voice.source = discord.PCMVolumeTransformer(voice.source)
                        voice.source.volume = 0.10
                else:
                    self.players[ctx.guild.id].pop()
                    voice.play(self.players[ctx.guild.id][-1], after=lambda e: check_queue())
            else:
                return

        if not self.players[ctx.guild.id]: #for no songs in queue

            song_search = " ".join(query)
            if "www.youtube.com/watch?v=" in song_search:
                try:
                    player = await YTDLSource.from_url(ctx, song_search, loop=self.client.loop, stream=True)
                    self.players[ctx.guild.id].insert(0, player)
                    embed = discord.Embed(title="**" + player.title + "**", colour=discord.Color.dark_magenta(),
                                          url=f"https://www.youtube.com/watch?v={player.id}")
                    embed.set_author(name=str(ctx.author.name) + ": Now Playing",
                                     icon_url=ctx.author.avatar_url)
                    embed.set_thumbnail(url=player.imageurl)
                    embed.add_field(name="Duration", value=str(datetime.timedelta(seconds=round(player.duration))))
                    embed.add_field(name="Uploader", value=player.uploader)
                    await ctx.send(embed=embed)
                    ctx.voice_client.play(player, after=lambda e: check_queue())
                    return
                except youtube_dl.DownloadError:
                    await ctx.send("``omg man, i can't play that song. im so sorry 😔``")
                    return
                except AudioTooLongError:
                    return
                except LiveStreamError:
                    return

            searchlist = []
            urllist = []

            req = self.youtube.search().list(q=song_search, part='snippet', type='video', maxResults=10)
            searchres = req.execute()
            if len(searchres['items']) == 10:
                for items in searchres['items']:
                    searchlist.append(html.unescape(items['snippet']))
                    urllist.append(items['id']['videoId'])
            else:
                req = self.youtube.search().list(q="video|"+song_search, part='snippet', type='video', maxResults=10) #ensures we always get 10 results but videos  may be more general now
                searchres = req.execute()
                for items in searchres['items']:
                    searchlist.append(items['snippet'])
                    urllist.append(items['id']['videoId'])
            try:
                embed = discord.Embed(title="**Search Results:**", description="**[1]:** "+html.unescape(searchlist[0]['title'])
                                                                               + "\n**[2]:** "+html.unescape(searchlist[1]['title'])
                                                                               + "\n**[3]:** "+html.unescape(searchlist[2]['title'])
                                                                               + "\n**[4]:** "+html.unescape(searchlist[3]['title'])
                                                                               + "\n**[5]:** "+html.unescape(searchlist[4]['title'])
                                                                               + "\n**[6]:** "+html.unescape(searchlist[5]['title'])
                                                                               + "\n**[7]:** "+html.unescape(searchlist[6]['title'])
                                                                               + "\n**[8]:** "+html.unescape(searchlist[7]['title'])
                                                                               + "\n**[9]:** "+html.unescape(searchlist[8]['title'])
                                                                               + "\n**[10]:** "+html.unescape(searchlist[9]['title'])
                                      , colour=discord.Color.dark_magenta())
            except:
                await ctx.send("``idk, couldn't find anything.``")
                return
            embed.set_author(name=str(ctx.author.name)+": Picking a song", icon_url=ctx.author.avatar_url)  # client.user.avatar_url)
            embed.add_field(name="type 'cancel' to cancel request", value="**Select a number (1-10):**")
            search = await ctx.send(embed=embed)
            self.active[ctx.guild.id] = True
            try:
                async with timeout(20):
                    while True:
                        msg = await self.client.wait_for('message', check=lambda message: message.author == ctx.author and message.channel == ctx.channel)
                        try:
                            if msg.content.upper() == "CANCEL":
                                break
                            elif int(msg.content) in range(1, 11):
                                break
                            else:
                                raise ValueError
                        except ValueError:
                            continue
            except asyncio.TimeoutError:
                self.active[ctx.guild.id] = False
                await search.delete()
                await ctx.send("❌"+" ``man, you didn't choose a song in time.``")
                return
            if msg.content.upper() == "CANCEL":
                msg = None
                await search.delete()
                await ctx.send("❌" + " ``ok canceled.``")
                self.active[ctx.guild.id] = False
                return
            if searchlist[int(msg.content) - 1]['liveBroadcastContent'] == "live":
                await search.delete()
                await ctx.send("``I can't play livestreams dude.``")
                self.active[ctx.guild.id] = False
                return

            async with ctx.typing():
                try:
                    player = await YTDLSource.from_url(ctx, f"https://www.youtube.com/watch?v={urllist[int(msg.content)-1]}", loop=self.client.loop, stream=True)
                except AudioTooLongError:
                    self.active[ctx.guild.id] = False
                    await search.delete()
                    return
                self.players[ctx.guild.id].insert(0, player)
                embed = discord.Embed(title="**"+player.title+"**", colour=discord.Color.dark_magenta(), url=f"https://www.youtube.com/watch?v={player.id}")
                embed.set_author(name=str(ctx.author.name) + ": Now Playing", icon_url=ctx.author.avatar_url)#client.user.avatar_url)
                embed.set_thumbnail(url=player.imageurl)
                embed.add_field(name="Duration", value=str(datetime.timedelta(seconds=round(player.duration))))
                embed.add_field(name="Uploader", value=player.uploader)
                await search.delete()
            await ctx.send(embed=embed)
            ctx.voice_client.play(player, after=lambda e: check_queue())
            self.active[ctx.guild.id] = False

        elif self.players[ctx.guild.id]: #songs in queue

            song_search = " ".join(query)
            if "www.youtube.com/watch?v=" in song_search:
                try:
                    player = await YTDLSource.from_url(ctx, song_search, loop=self.client.loop, stream=True)
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
                except AudioTooLongError:
                    self.active[ctx.guild.id] = False
                    return
                except LiveStreamError:
                    self.active[ctx.guild.id] = False
                    return

            searchlist = [] #has all the results
            urllist = [] #for video id for player

            req = self.youtube.search().list(q=song_search, part='snippet', type='video', maxResults=10)
            searchres = req.execute()
            if len(searchres['items']) == 10:
                for items in searchres['items']:
                    searchlist.append(html.unescape(items['snippet']))
                    urllist.append(items['id']['videoId'])
            else:
                req = self.youtube.search().list(q="video|"+song_search, part='snippet', type='video', maxResults=10) #ensures we always get 10 results but videos  may be more general now
                searchres = req.execute()
                for items in searchres['items']:
                    searchlist.append(items['snippet'])
                    urllist.append(items['id']['videoId'])
            try:
                embed = discord.Embed(title="**Search Results:**", description="**[1]:** "+html.unescape(searchlist[0]['title'])
                                                                               + "\n**[2]:** "+html.unescape(searchlist[1]['title'])
                                                                               + "\n**[3]:** "+html.unescape(searchlist[2]['title'])
                                                                               + "\n**[4]:** "+html.unescape(searchlist[3]['title'])
                                                                               + "\n**[5]:** "+html.unescape(searchlist[4]['title'])
                                                                               + "\n**[6]:** "+html.unescape(searchlist[5]['title'])
                                                                               + "\n**[7]:** "+html.unescape(searchlist[6]['title'])
                                                                               + "\n**[8]:** "+html.unescape(searchlist[7]['title'])
                                                                               + "\n**[9]:** "+html.unescape(searchlist[8]['title'])
                                                                               + "\n**[10]:** "+html.unescape(searchlist[9]['title'])
                                      , colour=discord.Color.dark_magenta())
            except:
                await ctx.send("``idk, couldn't find anything.``")
                return
            embed.set_author(name=str(ctx.author.name) + ": Picking a song",
                             icon_url=ctx.author.avatar_url)  # client.user.avatar_url)
            embed.add_field(name="type 'cancel' to cancel request", value="**Select a number (1-10):**")
            search = await ctx.send(embed=embed)
            self.active[ctx.guild.id] = True
            try:
                async with timeout(20):
                    while True:
                        msg = await self.client.wait_for('message', check=lambda
                            message: message.author == ctx.author and message.channel == ctx.channel)
                        try:
                            if msg.content.upper() == "CANCEL":
                                break
                            elif int(msg.content) in range(1, 11):
                                break
                            else:
                                raise ValueError
                        except ValueError:
                            continue
            except asyncio.TimeoutError:
                self.active[ctx.guild.id] = False
                await search.delete()
                await ctx.send("❌" + " ``man, you didn't choose a song in time.``")
                return
            if msg.content.upper() == "CANCEL":
                msg = None
                await search.delete()
                await ctx.send("❌" + " ``ok canceled.``")
                self.active[ctx.guild.id] = False
                return
            if searchlist[int(msg.content) - 1]['liveBroadcastContent'] == "live":
                await search.delete()
                await ctx.send("``I can't play livestreams dude.``")
                self.active[ctx.guild.id] = False
                return

            async with ctx.typing():
                try:
                    player = await YTDLSource.from_url(ctx,
                    f"https://www.youtube.com/watch?v={urllist[int(msg.content) - 1]}", loop=self.client.loop,
                    stream=True)
                except AudioTooLongError:
                    self.active[ctx.guild.id] = False
                    await search.delete()
                    return

                self.players[ctx.guild.id].insert(0, player)
                embed = discord.Embed(title="**"+player.title+"**", colour=discord.Color.dark_magenta(), url=f"https://www.youtube.com/watch?v={player.id}")
                embed.set_author(name=str(ctx.author.name) + ": Adding a song", icon_url=ctx.author.avatar_url)
                embed.set_thumbnail(url=player.imageurl)
                embed.add_field(name="Duration", value=str(datetime.timedelta(seconds=round(player.duration))))
                embed.add_field(name="Position in queue", value=str(len(self.players[ctx.guild.id])-1))
                embed.add_field(name="Uploader", value=player.uploader)
                await search.delete()
            await ctx.send(embed=embed)
            self.active[ctx.guild.id] = False

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
                    embed.add_field(name="Was in queue position", value=str(skip[0]))
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("``yup, sure, let me remove this non-existent song.``")
            else:
                await ctx.send("``bruh, i need a song in the queue to remove it.``")
        else:
            await ctx.send("``remove what song?``")

    @commands.command(pass_context=True, aliases=['replay'])
    async def restart(self, ctx):
        """- ShaneBot will restart any playing song"""
        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice:
            if self.players[ctx.guild.id]:
                self.restart[ctx.guild.id] = True
                await ctx.send("⏮"+f" ``{self.players[ctx.guild.id][-1].title}.``")
                voice.stop()
            else:
                await ctx.send("``no song to skip man.......``")
        else:
            await ctx.send("``r u stupid? im not even in a voice channel.``")

    @play.before_invoke
    @search.before_invoke
    async def voice_connected(self, ctx):

        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice:
            return
        else:
            try:
                channel = ctx.message.author.voice.channel
                voice = get(self.client.voice_clients, guild=ctx.guild)
            except AttributeError:
                await ctx.send("``man where am i going to play it huh? join channel first idot.``")
                return

            chperms = channel.permissions_for(ctx.guild.me)
            if not chperms.connect:  # no channel perms
                await ctx.send("😢" + " ``mannnn, i don't have the permission to join that channel.``")
                return
            if channel.user_limit != 0 and (len(channel.members) >= channel.user_limit):
                if chperms.connect and (chperms.move_members or chperms.administrator):
                    pass
                else:
                    await ctx.send("😭" + " ``there is not enough room for me man, ttyl.``")
                    return
            if voice is not None:
                await voice.move_to(channel)
                return
            await channel.connect()
            self.client.loop.create_task(self.disconnectTimer(ctx))

    async def disconnectTimer(self, ctx): #ensures if bot is not in use, it'll leave
        await self.client.wait_until_ready()
        voice = get(self.client.voice_clients, guild=ctx.guild)
        await asyncio.sleep(1000)
        while voice.is_playing():
            await asyncio.sleep(1200)#will check if anyone is same voice channel too
            i = 0
            for name in voice.channel.members:
                if i >= 1:
                    break
                elif name.bot:
                    continue
                else:
                    i += 1
            if i == 0:
                await voice.disconnect()
                self.players[ctx.guild.id].clear()
                self.repeatO[ctx.guild.id] = False
                self.repeatAll[ctx.guild.id] = False
                return
        self.players[ctx.guild.id].clear()
        self.repeatO[ctx.guild.id] = False
        self.repeatAll[ctx.guild.id] = False
        await voice.disconnect()


def setup(client):
    client.add_cog(Music(client))
