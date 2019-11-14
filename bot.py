import discord
from discord.ext import commands
from discord.utils import get
import random
import youtube_dl
import os
import shutil
import datetime

client = commands.Bot(command_prefix='ur ')
@client.event
async def on_guild_join(guild):
    print(str(guild.id))


'#TEXT STUFF-----------------------------------------------------------------------------------------------------------------------------------------------------------------'
@client.event
async def on_message(message):

    if message.content != "SHANER" and message.content.capitalize() == "Shaner":
        await message.channel.send("what do you want man")
    if message.content.find("SHANER") != -1:
        await message.channel.send("MAN WHAT DO U WANT?")
    if message.content.upper() == "KISS":
        suslist = ["i want you to interlock lips with me", "omg kiss me omg", "pls kiss me man", "ur have succulent lips man", "no ty, fgt stay in ur lane"]
        susit = random.randint(0,3)
        await message.channel.send(suslist[susit])
    if (message.content.upper() == "HEY SHANER"):
        if str(message.author.id) == "168603442175148032":
            await message.channel.send("omg, yes master?")
        elif str(message.author.id) == "234743458961555459":
            await message.channel.send("hey daddy jerry")
        else:
            mesgaut = (str(message.author)).split("#")
            print(str(message.author.id))
            await message.channel.send(f"ok hey, **{mesgaut[0]}**")

    await client.process_commands(message)


#@client.event
#async def on_command_error(error, ctx):
    #await error.channel.send("`there was an error.\nomg ur broke me :(`")

'#VOICE STUFF (MUSIC)----------------------------------------------------------------------------------------------------------------------------------------------------------------'

queues = []

@client.event
async def on_ready():
    print('client ready')
    await client.change_presence(status=discord.Status.online, activity=discord.Game("ur pls invite me"))

@client.command(pass_context=True)
async def join(ctx):

    global voice, channel

    try:
        channel = ctx.message.author.voice.channel
        voice = get(client.voice_clients, guild=ctx.guild)
    except AttributeError:
        await ctx.send("`ur know i cant join if ur're not in channel, right?`")
        return

    if voice is not None:
        return await voice.move_to(channel)
    await channel.connect()
    await ctx.send(f"`ok man, i joined: {channel}.`")

@client.command(pass_context=True)
async def leave(ctx):

    voice = get(client.voice_clients, guild=ctx.guild)
    channel = ctx.message.author.voice.channel

    if voice and voice.is_connected():
        await voice.disconnect()
        await ctx.send(f"`ok, i left: {channel}.`")
    else:
        await ctx.send("`man ur know im not connected to a channel, idot.`")


@client.command(pass_context=True)
async def pause(ctx):

    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing():
        voice.pause()
        await ctx.send("`ok, paused.`")
    else:
        await ctx.send("`no music playing so ill just pause myself.`")


@client.command(pass_context=True)
async def resume(ctx):

    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_paused():
        voice.resume()
        await ctx.send("`ok i resume, ur welcome.`")
    else:
        await ctx.send("`ok ill resume nothing, idot.`")

@client.command(pass_context=True)
async def stop(ctx):

    queues.clear()
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing():
        voice.stop()
        await ctx.send("`ok i stopped ur song`")
    else:
        await ctx.send("`no song to stop. if only i can stop you from being an idot`")

@client.command(pass_context=True, aliases = ['p', 'search'])
async def play(ctx, *url: str):

    if len(url) < 1:
        await ctx.send("``play what song man? enter youtube url or search.``")
        return

    if ("&list" in url[0]) and ("youtube.com/watch?" in url[0]):
        await ctx.send("``I dont currently support playlist, sorry man :(``")
        return

    for emotion in url:
        if "SAD" == emotion.upper():
            await ctx.send("``hey man ur good? dont worry man im here for ur.``")
        if "HAPPY" == emotion.upper():
            await ctx.send("``omg ur happy? me 2 man.``")

    voice = get(client.voice_clients, guild=ctx.guild)

    try:
        channel = ctx.message.author.voice.channel
        if voice is not None:
            await voice.move_to(channel)
        else:
            await channel.connect()
    except AttributeError:
        await ctx.send("``man where am i going to play it huh? join channel first idot.``")
        return

    voice = get(client.voice_clients, guild=ctx.guild)
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
                       'postprocessors': [{
                           'key': 'FFmpegExtractAudio',
                           'preferredcodec': 'mp3',
                           'preferredquality': '192',
                           }],
        }

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
                                    queues.insert(0, videoData['title']+"`|`"+(filechange.split(".mp3"))[0]+"`|`"+videoData['webpage_url']+"`|`"+videoData['thumbnail'])
                                    break
                        else:
                            main_location = os.path.dirname(os.path.realpath("./Queue/QueueQueue"))
                            main_location = os.path.join(main_location, 'QueueQueue')
                            song_path = os.path.abspath(os.path.realpath("Queue" + "\\" + file))
                            shutil.move(song_path, main_location)
                            videoData = ydl.extract_info(mfile[0], download=False)
                            queues.insert(0, videoData['title']+"`|`"+videoData['id']+"`|`"+videoData['webpage_url']+"`|`"+videoData['thumbnail'])

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
                print(queues)

                if len(os.listdir(DIR)) == 0: #for only one song added to queue
                    if len(os.listdir(os.path.abspath(os.path.realpath("./Play")))) == 1:
                        queues.pop()
                        for Pfile in os.listdir("./Play"):
                            os.remove("./Play\\"+Pfile)
                    songnext = queues[Queuelength - 1].split("`|`")
                    songmv = os.path.abspath(os.path.realpath("Queue" + "\\" + "QueueQueue" + "\\" + songnext[1] + ".mp3"))
                    mainlocation = os.path.dirname(os.path.realpath("./Queue/QueuePlay"))
                    mainlocation = os.path.join(mainlocation, 'QueuePlay')
                    shutil.move(songmv, mainlocation)

                else:
                    queues.pop()
                    for songrm in os.listdir("./Queue/QueuePlay"):
                        os.remove(DIR+"/"+songrm)
                    if queues is False:
                        return
                    songnext = queues[Queuelength-1].split("`|`")
                    songmv = os.path.abspath(os.path.realpath("Queue" + "\\" + "QueueQueue" + "\\" + songnext[1]+".mp3"))
                    mainlocation = os.path.dirname(os.path.realpath("./Queue/QueuePlay"))
                    mainlocation = os.path.join(mainlocation, 'QueuePlay')
                    shutil.move(songmv, mainlocation)

                voice.play(discord.FFmpegPCMAudio(DIR+"/"+songnext[1]+".mp3"), after=lambda e: check_queue())
                voice.source = discord.PCMVolumeTransformer(voice.source)
                voice.source.volume = 0.25

            else:
                queues.clear()

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
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        async with ctx.typing():
            song_search = " ".join(url)
            await ctx.send("**Searching Youtube: **``" + song_search + "``")
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([f"ytsearch1:{song_search}"])
                except:
                    await ctx.send("``Weird Issue, please try again.``")
                for file in os.listdir("./Play"):
                    pfile = file.split(".mp3")
                videoData = ydl.extract_info(pfile[0], download=False)
                queues.insert(0, videoData['title'] + "`|`" + videoData['id'] + "`|`" + videoData['webpage_url']+"`|`"+videoData['thumbnail'])
        voice = get(client.voice_clients, guild=ctx.guild)
        voice.play(discord.FFmpegPCMAudio("Play/"+videoData['id']+".mp3"), after=lambda e: check_queue())
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = 0.25

        embed = discord.Embed(title="**"+videoData['title']+"**", colour=discord.Color.blue(), url=videoData['webpage_url'])
        embed.set_author(name=str(ctx.author.name) + ": Now Playing", icon_url=ctx.author.avatar_url)#client.user.avatar_url)
        embed.set_thumbnail(url=videoData['thumbnail'])
        embed.add_field(name="Duration", value=str(datetime.timedelta(seconds=round(videoData['duration']))))
        embed.add_field(name="Uploader", value=videoData['uploader'])
        await ctx.send(embed=embed)

@client.command(pass_context=True, aliases = ['next'])
async def skip(ctx):

    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing():
        voice.stop()
        await ctx.send("`ok i skipped`")
    else:
        await ctx.send("`no song to skip??????????`")

@client.command(pass_context=True,aliases =['vol'])
async def volume(ctx, volume: int):

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

@client.command(pass_context=True,aliases =['q'])
async def queue(ctx):

    if len(queues) == 1:
        embed = discord.Embed(title="**"+(queues[len(queues)-1].split("`|`"))[0]+"**", description="**Playing Now**",
                              url=(queues[len(queues)-1].split("`|`"))[2],
                              colour=discord.Color.purple())
        embed.set_thumbnail(url=(queues[len(queues)-1].split("`|`"))[3])
        await ctx.send(embed=embed)
    else:
        pos = 1
        length = len(queues)-1
        embed = discord.Embed(title="**__Now Playing:__ "+(queues[length].split("`|`"))[0]+"**",
                              description="\n\n**Currently In Queue:**",url=(queues[length].split("`|`"))[2],
                              colour=discord.Color.purple())
        embed.set_thumbnail(url=(queues[length].split("`|`"))[3])
        embed.set_author(name=client.user.name, icon_url=client.user.avatar_url)
        for num in range(length):
            item = queues[(length-1)-num].split("`|`")
            embed.add_field(name="**["+str(pos)+"] "+item[0]+"**", value=""+item[2], inline=False)
            pos += 1
        await ctx.send(embed=embed)

client.run("token")