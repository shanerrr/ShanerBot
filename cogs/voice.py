import discord
from discord.ext import commands
from discord.utils import get
import youtube_dl
import os
from os import system
import shutil
import datetime
import sqlite3



class Music(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.queues = []

        DIR = os.path.dirname(__file__)
        self.db = sqlite3.connect(
            os.path.join(DIR, "ServerID.db"))  # connecting to DB if this file is not there it will create it
        self.SQL = self.db.cursor()

    def database(self, ctx):
        self.SQL.execute('create table if not exists Music('
                    '"Num" integer not null primary key autoincrement, '
                    '"Server_ID" integer, '
                    '"Server_Name" text, '
                    '"Voice_ID" integer, '
                    '"Voice_Name" text, '
                    '"User_Name" text, '
                    '"Next_Queue" integer, '
                    '"Queue_Name" text, '
                    '"Song_Name" text'
                    ')')
        server_name = str(ctx.guild)
        print(server_name)
        server_id = ctx.guild.id
        user_name = str(ctx.message.author)
        queue_name = f"Queue#{server_id}"
        song_name = f"Song#{server_id}"
        channel_id = ctx.message.author.voice.channel.id
        channel_name = str(ctx.message.author.voice.channel)
        queue_num = 1
        self.SQL.execute(
            'insert into Music(Server_ID, Server_Name, Voice_ID, Voice_Name, User_Name, Next_Queue, Queue_Name, Song_Name) values(?,?,?,?,?,?,?,?)',
            (server_id, server_name, channel_id, channel_name, user_name, queue_num, queue_name, song_name))
        self.db.commit()

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

        #if ("&list" in url[0]) and ("youtube.com/watch?" in url[0]):
            #await ctx.send("``I dont currently support playlist, sorry man :(``")
            #return

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
            Queue_infile = os.path.isdir("./Queue")
            if Queue_infile is False:
                os.mkdir("Queue")
                os.mkdir("./Queue/QueuePlay")
                os.mkdir("./Queue/QueueQueue")
            DIR = os.path.abspath(os.path.realpath("./Queue/QueueQueue"))
            queuenum = len(os.listdir(DIR))

            queue_path = os.path.abspath(os.path.realpath("./Queue") + "\%(id)s.%(ext)s")

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
                    for file in os.listdir("./Queue"):
                        if file.endswith(".mp3"):
                            mfile = file.split(".mp3")
                            if os.path.isfile("./Queue/QueueQueue"+"\\"+file):
                                while True:
                                    filechange = "("+str(filecount)+")"+file
                                    if os.path.isfile("./Queue/QueueQueue" + "\\" + filechange):
                                        filecount += 1
                                        continue
                                    else:
                                        main_location = os.path.dirname(os.path.realpath("./Queue/QueueQueue"))
                                        os.rename(os.path.join(main_location, file), os.path.join(main_location, filechange))
                                        main_location = os.path.join(main_location, 'QueueQueue')
                                        song_path = os.path.abspath(os.path.realpath("Queue" + "\\" + filechange))
                                        shutil.move(song_path, main_location)
                                        videoData = ydl.extract_info(mfile[0], download=False)
                                        self.queues.insert(0, videoData['title']+"`|`"+(filechange.split(".mp3"))[0]+"`|`"+videoData['webpage_url']+"`|`"+videoData['thumbnail'])
                                        break
                            else:
                                main_location = os.path.dirname(os.path.realpath("./Queue/QueueQueue"))
                                main_location = os.path.join(main_location, 'QueueQueue')
                                song_path = os.path.abspath(os.path.realpath("Queue" + "\\" + file))
                                shutil.move(song_path, main_location)
                                videoData = ydl.extract_info(mfile[0], download=False)
                                self.queues.insert(0, videoData['title']+"`|`"+videoData['id']+"`|`"+videoData['webpage_url']+"`|`"+videoData['thumbnail'])

            embed = discord.Embed(title="**"+videoData['title']+"**", colour=discord.Color.blue(), url=videoData['webpage_url'])
            embed.set_author(name=str(ctx.author.name) + ": Adding a song", icon_url=ctx.author.avatar_url)#client.user.avatar_url)
            embed.set_thumbnail(url=videoData['thumbnail'])
            embed.add_field(name="Duration", value=str(datetime.timedelta(seconds=round(videoData['duration']))))
            embed.add_field(name="Position in queue", value=str(queuenum+1))
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
                Queue_infile = os.path.isdir("./Queue/QueueQueue")
                if Queue_infile is True:
                    DIR = os.path.abspath(os.path.realpath("./Queue/QueuePlay"))
                    DIRQueue = os.path.abspath(os.path.realpath("./Queue/QueueQueue"))
                    Queuelength = len(os.listdir(DIRQueue))
                    print(self.queues)

                    if len(os.listdir(DIR)) == 0: #for only one song added to queue
                        if len(os.listdir(os.path.abspath(os.path.realpath("./Play")))) == 1:
                            self.queues.pop()
                            for Pfile in os.listdir("./Play"):
                                os.remove("./Play\\"+Pfile)
                        songnext = self.queues[Queuelength - 1].split("`|`")
                        songmv = os.path.abspath(os.path.realpath("Queue" + "\\" + "QueueQueue" + "\\" + songnext[1] + ".mp3"))
                        mainlocation = os.path.dirname(os.path.realpath("./Queue/QueuePlay"))
                        mainlocation = os.path.join(mainlocation, 'QueuePlay')
                        shutil.move(songmv, mainlocation)

                    else:
                        self.queues.pop()
                        for songrm in os.listdir("./Queue/QueuePlay"):
                            os.remove(DIR+"/"+songrm)
                        if self.queues is False:
                            return
                        songnext = self.queues[Queuelength-1].split("`|`")
                        songmv = os.path.abspath(os.path.realpath("Queue" + "\\" + "QueueQueue" + "\\" + songnext[1]+".mp3"))
                        mainlocation = os.path.dirname(os.path.realpath("./Queue/QueuePlay"))
                        mainlocation = os.path.join(mainlocation, 'QueuePlay')
                        shutil.move(songmv, mainlocation)

                    voice.play(discord.FFmpegPCMAudio(DIR+"/"+songnext[1]+".mp3"), after=lambda e: check_queue())
                    voice.source = discord.PCMVolumeTransformer(voice.source)
                    voice.source.volume = 0.25

                else:
                    self.queues.clear()

            Queue_infile = os.path.isdir("./Queue")  # checks old queue folder and deletes it
            try:
                Queue_folder = "./Queue"
                if Queue_infile is True:
                    shutil.rmtree(Queue_folder)
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
                        print(song_search)
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

    @commands.command(pass_context=True, aliases = ['next'])
    async def skip(self, ctx):

        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_playing():
            voice.stop()
            await ctx.send("`ok i skipped`")
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

    @commands.command(pass_context=True, aliases =['q'])
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
                                  description="\n\n**Currently In Queue:**",url=(self.queues[length].split("`|`"))[2],
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