import discord
from discord.ext import commands
from discord.utils import get
import youtube_dl
import os
from os import system
import shutil
import datetime



class Music(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.queues = []

    @commands.command(pass_context=True)
    async def join(self, ctx):

        global voice, channel

        try:
            channel = ctx.message.author.voice.channel
            voice = get(self.client.voice_clients, guild=ctx.guild)
        except AttributeError:
            await ctx.send("`ur know i cant join if ur're not in channel, right?`")
            return

        if voice is not None:
            return await voice.move_to(channel)
        await channel.connect()
        await ctx.send(f"`ok man, i joined: {channel}.`")

        print(ctx.guild.id)

    @commands.command(pass_context=True)
    async def leave(self, ctx):

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_connected():
            await voice.disconnect()
            await ctx.send(f"`ok, i left: {voice.channel}.`")
        else:
            await ctx.send("`man ur know im not connected to a channel, idot.`")


    @commands.command(pass_context=True)
    async def pause(self, ctx):

        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_playing():
            voice.pause()
            await ctx.send("`ok, paused.`")
        else:
            await ctx.send("`no music playing so ill just pause myself.`")


    @commands.command(pass_context=True)
    async def resume(self, ctx):

        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_paused():
            voice.resume()
            await ctx.send("`ok i resume, ur welcome.`")
        else:
            await ctx.send("`ok ill resume nothing, idot.`")

    @commands.command(pass_context=True)
    async def stop(self, ctx):

        self.queues.clear()
        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_playing():
            voice.stop()
            await ctx.send("`ok i stopped ur song`")
        else:
            await ctx.send("`no song to stop. if only i can stop you from being an idot`")

    @commands.command(pass_context=True, aliases = ['p', 'search'])
    async def play(self, ctx, *url: str):

        if len(url) < 1:
            await ctx.send("``play what song man? enter youtube url or search.``")
            return

        for emotion in url:
            if "SAD" == emotion.upper():
                await ctx.send("``hey man ur good? dont worry man im here for ur.``")
            if "HAPPY" == emotion.upper():
                await ctx.send("``omg ur happy? me 2 man.``")

        voice = get(self.client.voice_clients, guild=ctx.guild)

        try:
            channel = ctx.message.author.voice.channel
            if voice is not None:
                await voice.move_to(channel)
            else:
                await channel.connect()
        except AttributeError:
            await ctx.send("``man where am i going to play it huh? join channel first idot.``")
            return

        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice.is_playing() or voice.is_paused():

            DIR = os.path.abspath(os.path.realpath("./Play"))
            queuenum = len(os.listdir(DIR))

            queue_path = os.path.abspath(os.path.realpath("./") + "\%(id)s.%(ext)s")

            ydl_opts = {
                           'format': 'bestaudio/best',
                           'quiet': True,
                           'outtmpl': queue_path,
                           'noplaylist': True,
                           'postprocessors': [{
                               'key': 'FFmpegExtractAudio',
                               'preferredcodec': 'mp3',
                               'preferredquality': '192',
                               }],
            }

            if "&list=" in url[0]:
                song_search = (url[0].split("&list="))[0]
                await ctx.send("**Searching Youtube:** ``" + song_search + "``")
            else:
                song_search = " ".join(url)
                await ctx.send("**Searching Youtube:** ``"+song_search+"``")

            filecount = 0
            async with ctx.typing():
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    try:
                        ydl.download([f"ytsearch1:{song_search}"])
                    except:
                        await ctx.send("``Weird Issue, please try again.``")
                    for file in os.listdir("./"):
                        if file.endswith(".mp3"):
                            mfile = file.split(".mp3")
                            if os.path.isfile("./Play"+"/"+file):
                                while True:
                                    filechange = str(filecount)+file
                                    if os.path.isfile("./Play" + "/" + filechange):
                                        filecount += 1
                                        continue
                                    else:
                                        main_location = os.path.dirname(os.path.realpath("Play"))
                                        os.rename(os.path.join(main_location, file), os.path.join(main_location, filechange))
                                        main_location = os.path.join(main_location, 'Play')
                                        song_path = os.path.abspath(os.path.realpath(filechange))
                                        shutil.move(song_path, main_location)
                                        videoData = ydl.extract_info(mfile[0], download=False)
                                        self.queues.insert(0, videoData['title']+"`|`"+(filechange.split(".mp3"))[0]+"`|`"+videoData['webpage_url']+"`|`"+videoData['thumbnail'])
                                        break
                            else:
                                main_location = os.path.dirname(os.path.realpath("./Play"))
                                #main_location = os.path.join(main_location, 'QueueQueue')
                                song_path = os.path.abspath(os.path.realpath("./" + "\\" + file))
                                shutil.move(song_path, main_location)
                                videoData = ydl.extract_info(mfile[0], download=False)
                                self.queues.insert(0, videoData['title']+"`|`"+videoData['id']+"`|`"+videoData['webpage_url']+"`|`"+videoData['thumbnail'])

            embed = discord.Embed(title="**"+videoData['title']+"**", colour=discord.Color.blue(), url=videoData['webpage_url'])
            embed.set_author(name=str(ctx.author.name) + ": Adding a song", icon_url=ctx.author.avatar_url)#client.user.avatar_url)
            embed.set_thumbnail(url=videoData['thumbnail'])
            embed.add_field(name="Duration", value=str(datetime.timedelta(seconds=round(videoData['duration']))))
            embed.add_field(name="Position in queue", value=str(queuenum))
            embed.add_field(name="Uploader", value=videoData['uploader'])
            #implement duration in queue
            await ctx.send(embed=embed)

        elif (voice.is_playing() is False) and (voice.is_paused() is False): #------------------------------------------------------------------------------------------------

            try:
                for fileplay in os.listdir("./Play"):
                    os.remove("Play/" + fileplay)
            except FileNotFoundError:
                os.mkdir("Play")

            def check_queue():
                Queue_infile = os.path.isdir("./Play")
                if Queue_infile is True:
                    DIR = os.path.abspath(os.path.realpath("./Play"))
                    Queuelength = len(os.listdir(DIR))

                    if Queuelength != 0:
                        songdelete = self.queues.pop()
                        os.remove(DIR+"/"+(songdelete.split("`|`"))[1]+".mp3")
                        songnext = self.queues[Queuelength - 2].split("`|`")
                    else:
                        self.queues.clear()
                        return

                    voice.play(discord.FFmpegPCMAudio(DIR+"/"+songnext[1]+".mp3"), after=lambda e: check_queue())
                    voice.source = discord.PCMVolumeTransformer(voice.source)
                    voice.source.volume = 0.25

                else:
                    self.queues.clear()

            Queue_infile = os.path.isdir("./Play")  # checks old queue folder and deletes it
            try:
                Queue_folder = "./Play"
                if Queue_infile is True:
                    shutil.rmtree(Queue_folder)
                    for file in os.listdir("./"):
                        os.remove(file.endswith(".mp3"))
            except:
                pass

            play_path = os.path.abspath(os.path.realpath("Play") + "\%(id)s.%(ext)s")
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'outtmpl': play_path,
                'noplaylist': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }

            if "&list=" in url[0]:
                song_search = (url[0].split("&list="))[0]
                await ctx.send("**Searching Youtube:** ``" + song_search + "``")
            else:
                song_search = " ".join(url)
                await ctx.send("**Searching Youtube:** ``"+song_search+"``")

            async with ctx.typing():
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    try:
                        ydl.download([f"ytsearch1:{song_search}"])
                        #system(f"youtube-dl ytsearch1:{song_search} --no-playlist --write-info-json --skip-download")

                    except:
                        await ctx.send("``Weird Issue, please try again.``")
                    for file in os.listdir("./Play"):
                        pfile = file.split(".mp3")
                    videoData = ydl.extract_info(pfile[0], download=False)
                    self.queues.insert(0, videoData['title'] + "`|`" + videoData['id'] + "`|`" + videoData['webpage_url']+"`|`"+videoData['thumbnail'])
            voice = get(self.client.voice_clients, guild=ctx.guild)
            voice.play(discord.FFmpegPCMAudio("Play/"+videoData['id']+".mp3"), after=lambda e: check_queue())
            voice.source = discord.PCMVolumeTransformer(voice.source)
            voice.source.volume = 0.25

            embed = discord.Embed(title="**"+videoData['title']+"**", colour=discord.Color.blue(), url=videoData['webpage_url'])
            embed.set_author(name=str(ctx.author.name) + ": Now Playing", icon_url=ctx.author.avatar_url)#client.user.avatar_url)
            embed.set_thumbnail(url=videoData['thumbnail'])
            embed.add_field(name="Duration", value=str(datetime.timedelta(seconds=round(videoData['duration']))))
            embed.add_field(name="Uploader", value=videoData['uploader'])
            await ctx.send(embed=embed)

    @commands.command(pass_context=True, aliases=['next'])
    async def skip(self, ctx):

        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_playing():
            songskip = (self.queues[-1]).split("`|`")
            embed = discord.Embed(title="**" + songskip[0] + "**", colour=discord.Color.dark_green(),
                                  url=songskip[3])
            embed.set_author(name=str(ctx.author.name) + ": Skipped a song",
                             icon_url=ctx.author.avatar_url)  # client.user.avatar_url)
            embed.set_thumbnail(url=songskip[3])
            await ctx.send(embed=embed)
            voice.stop() #stops song and starts next song if there is any song queued

        else:
            await ctx.send("`no song to skip??????????`")

    @commands.command(pass_context=True, aliases =['vol'])
    async def volume(self, ctx, volume: int):

        if volume is None:
            return await ctx.send("`hey man, u need to put a number in, u know, to change the volume, idot.`")
        if ctx.voice_client is None:
            return await ctx.send("`hey man, cant really change volume if im not in a channel hahaha idot.`")
        if ctx.voice_client.source is None:
            return await ctx.send("`yeah man, ill changed the volume of this imaginary song, k did it.`")
        if volume > 100:
            await ctx.send("`ur must be a different kind of stupid, ur want more than 100%? idot pls ur idot.`")
            return
        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"`ur got it, volume is now at {volume}%`")

    @commands.command(pass_context=True, aliases=['q'])
    async def queue(self, ctx):

        if len(self.queues) == 0:
            await ctx.send("`bruh, nothing in queue.`")
            return
        if len(self.queues) == 1:
            embed = discord.Embed(title="**"+(self.queues[len(self.queues)-1].split("`|`"))[0]+"**", description="**Playing Now**",
                                  url=(self.queues[len(self.queues)-1].split("`|`"))[2],
                                  colour=discord.Color.dark_red())
            embed.set_thumbnail(url=(self.queues[len(self.queues)-1].split("`|`"))[3])
            await ctx.send(embed=embed)
        else:
            pos = 1
            length = len(self.queues)-1
            embed = discord.Embed(title="**__Now Playing:__ "+(self.queues[length].split("`|`"))[0]+"**",
                                  description="\n\n**Currently In Queue:**", url=(self.queues[length].split("`|`"))[2],
                                  colour=discord.Color.purple())
            embed.set_thumbnail(url=(self.queues[length].split("`|`"))[3])
            embed.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
            for num in range(length):
                item = self.queues[(length-1)-num].split("`|`")
                embed.add_field(name="**["+str(pos)+"] "+item[0]+"**", value=""+item[2], inline=False)
                pos += 1
            await ctx.send(embed=embed)


def setup(client):
    client.add_cog(Music(client))