import asyncio
from . import queuing
import discord
import itertools
import datetime
import re
import wavelink
from discord.ext import commands
from typing import Union
import datetime as dt
from random import shuffle
from math import ceil
import json
import requests
from lyricsgenius import Genius
from discord.ext import menus
from async_timeout import timeout
import spotify

pattern = re.compile(r'(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?')
SPOTIFY_URL_REG = re.compile(r'https?://open.spotify.com/(?P<type>album|playlist|track)/(?P<id>[a-zA-Z0-9]+)')

class Track(wavelink.Track):
    """Wavelink Track object with a requester attribute."""

    __slots__ = ('requester', 'pn')

    def __init__(self, *args, **kwargs):
        super().__init__(*args)

        self.requester = kwargs.get('requester')
        self.pn= kwargs.get('pn')

class MySource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page
        random_dict = {}

        # "\n".join(f"{i}. [{v}]({v.uri}) | `{dt.timedelta(milliseconds = v.length)}`\n"
        for h in range(1,(len(entries)+ 1)):
            try:
                random_dict[h] = dt.timedelta(milliseconds = entries[h-1].length)
            except OverflowError:
                random_dict[h] = "🧿 live"

        fmt ='\n'.join(f"{i+1}. [{v}]({v.uri}) | `{random_dict[i+1]}`\n" for i, v in enumerate(entries, start=offset))

        # fmt ="\n".join(f"{i + 1}. [{v}]({v.uri}) | `{dt.timedelta(milliseconds = v.length)}`\n" for i,v in enumerate(entries, start=offset)
        embed = discord.Embed(title=f"Upcoming- {len(entries)}",description=fmt,
        color= discord.Color.from_rgb(132,112,255))
        embed.set_footer(text= f"• Page {menu.current_page + 1}")
        return embed

class MusicController:

    def __init__(self,ctx):
        self.ctx = ctx
        self.bot = ctx.bot
        self.guild_id = ctx.guild.id
        self.channel =  ctx.channel
        self.vc_channel = None
        self.queue = queuing.Queue()
        self.finished= queuing.Queue(maxsize=10)
        self.prev_loop = False
        self.duration = None
        self.pn_track = None
        self.prev =None
        self.loop_track= False
        self.genius = Genius('Zb2AEFCJL7r-nfdjbFeNViR9RoK82J0GxSsk53yQygB7v0u8Elt6UobXi_DUZXmJ')
        self.loop_queue = False
        self.volume = 60
        self.np = None
        self.waiting = False
        self.player = self.bot.wavelink.get_player(self.guild_id)
        self.wavelink = self.bot.wavelink


    async def set_vol(self,vol):
        await self.player.set_volume(vol)

    async def controller_loop(self):

        if self.player.is_playing or self.waiting:
            return
        await self.set_vol(self.volume)

        try:
            async with timeout(300):
                self.waiting= True

                if self.prev_loop:
                    song = self.finished._get_right()
                    self.prev_loop= False

                elif self.loop_track:
                    song = self.prev

                else:
                    song = await self.queue.get()

        except asyncio.TimeoutError:
            return self.destroy(self.ctx)


        if song.id == "spotify":
            spotify_tracks = await self.wavelink.get_tracks(f"ytsearch:{song.title} {song.author} audio")
            song = spotify_tracks[0]

        await self.player.play(song)
        self.prev = song

        if self.loop_queue:
            await self.queue.put(song)

        self.waiting = False

        passed = dt.timedelta(milliseconds = self.player.position)
        rounded = datetime.timedelta(seconds=round(passed.total_seconds()))
        try:
            self.duration = dt.timedelta(milliseconds = song.length)
        except OverflowError:
            self.duration = "🧿 live"

        upcoming = list(itertools.islice(self.queue._queue, 0, 1))
        tick_or_not= lambda x: "✔️" if x else "❌"

        if upcoming:
            try:
                fmt = "\n".join(f"[{_.title}]({_.uri}) | `{dt.timedelta(milliseconds = _.length)}`" for _ in upcoming)
            except OverflowError:
                fmt = "\n".join(f"[{_.title}]({_.uri}) | `🧿 live`" for _ in upcoming)
        else:
            fmt = "No other songs added to queue."

        try:
            embed = discord.Embed(title= f"{self.player.current.title}", url = f"{self.player.current.uri}",
            description = f"Duration: `{self.duration}`",
            color= discord.Color.from_rgb(132,112,255))
        except AttributeError:
            return

        #temporary thing
        if hasattr(self.player.current,"requester"):
            embed.set_author(name = f"Now Playing \nRequested by: {self.player.current.requester}")

        if self.player.current.thumb:
            embed.set_thumbnail(url=f"{self.player.current.thumb}")

        # embed.add_field(name= "Volume",value= f"{self.player.volume}",inline= True)
        # embed.add_field(name= "Queue",value= f"{self.queue.qsize()}")
        # embed.add_field(name = "Coming up next:", value= f'{fmt}', inline = False)
        # embed.set_footer(text= f"• Queue Loop: **{self.loop_queue}** | Track Loop: **{self.loop_track}**\n Type .np for an updated now playing message.")
        embed.set_footer(text= f"• Queue Loop: {tick_or_not(self.loop_queue)} | Track Loop: {tick_or_not(self.loop_track)} | Paused: {tick_or_not(self.player.is_paused)}")
        self.np = await self.channel.send(embed = embed)

    def destroy(self,ctx):
        return self.bot.loop.create_task(self.ctx.cog.cleanup(ctx))

    @commands.Cog.listener(name='on_voice_state_update')
    async def check_disconnect(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member == self.ctx.me:
            if before.channel is not None and after.channel is None:
                return self.bot.loop.create_task(self.ctx.cog.cleanup(ctx))

class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.controllers = {}

        self.spotify_client = spotify.Client("c0e3f0b9935a49daa7433052e5fecfb6","bc9e76bba91d42e9ab924ab5124698cb")
        self.spotify_http_client = spotify.HTTPClient("c0e3f0b9935a49daa7433052e5fecfb6","bc9e76bba91d42e9ab924ab5124698cb")
        self.channel = None

        if not hasattr(bot, 'wavelink'):
            self.bot.wavelink = wavelink.Client(bot=self.bot)

        self.bot.loop.create_task(self.start_nodes())

    async def start_nodes(self):
        await self.bot.wait_until_ready()

        # Initiate our nodes. For this example we will use one server.
        # Region should be a discord.py guild.region e.g sydney or us_central (Though this is not technically required)
        node = await self.bot.wavelink.initiate_node(host='127.0.0.1',
                                                     port=2333,
                                                     rest_uri='http://127.0.0.1:2333',
                                                     password='MrWonkapass',
                                                     identifier='MrWonka',
                                                     region='us_central')

        # Set our node hook callback
        node.set_hook(self.on_event_hook)

    def empty_queue(self,q: Union[asyncio.Queue,queuing.Queue]):
        for i in range(q.qsize()):
            q.get_nowait()
            q.task_done()

    async def on_track_end(self, node):
            ...

    async def cleanup(self,ctx):

        controller = self.get_controller(ctx)

        player= self.bot.wavelink.get_player(ctx.guild.id)

        if player.is_playing:
            await player.stop()

        try:
            await player.destroy()
        except:
            pass

        try:
            del self.controllers[ctx.guild.id]
        except KeyError:
            pass

    async def on_event_hook(self, event):
        """Node hook callback."""
        if isinstance(event, (wavelink.TrackEnd, wavelink.TrackException)):
            controller = self.get_controller(event.player)
            if len(controller.vc_channel.members) == 1:
                print(controller.vc_channel.members)
                return await controller.destroy(controller.ctx)

            # player = self.bot.wavelink.get_player(event.player.guild_id)
            # if isinstance(event,wavelink.TrackException):
            #     await self.channel.send("⚠️ There was an Error in processing the song, feel free to continue to listen to music.")

            if controller.prev_loop:
                pass

            elif controller.loop_track:
                pass

            else:
                try:
                    controller.finished.put_nowait(controller.prev)
                except queuing.QueueFull:
                    controller.finished.get_nowait()
                    controller.finished.task_done()
                    controller.finished.put_nowait(controller.prev)
            await controller.controller_loop()

    def get_controller(self, value: Union[commands.Context, wavelink.Player]):
        if isinstance(value, commands.Context):
            gid = value.guild.id
        else:
            gid = value.guild_id
        try:
            controller = self.controllers[gid]
        except KeyError:
            controller = MusicController(value)
            self.controllers[gid] = controller

        self.channel = controller.channel
        return controller

    async def single_song(self,ctx,controller,tracks,position):
        if position == "pn":
            track = Track(tracks[0].id, tracks[0].info, requester=ctx.author, pn= True)
            if controller.queue.empty():
                await controller.queue.put(track)
            else:
                controller.queue._put_left(track)
        else:
            track = Track(tracks[0].id, tracks[0].info, requester=ctx.author, pn= False)
            if controller.loop_queue:
                controller.queue._put_left(track)
            else:
                await controller.queue.put(track)
        if controller.loop_queue:
            return await ctx.send(f'```ini\n[Added {track.title} to the Loop.]\n```')
        else:
            embed = discord.Embed(title=track.title, description= "Added to Queue",
            color= discord.Color.from_rgb(132,112,255))
            return await ctx.send(embed = embed)

    async def process_request(self, position: str, ctx:commands.Context , source: str, query):

        controller = self.get_controller(ctx)
        matches = pattern.search(query)
        NoneType= type(None)

        if matches:
            query = query.strip('<>')
            if SPOTIFY_URL_REG.match(query):
                spoturl_check = SPOTIFY_URL_REG.match(query)
                search_type = spoturl_check.group('type')
                spotify_id = spoturl_check.group('id')

                if search_type == "playlist":
                    try:
                        results = spotify.Playlist(client=self.spotify_client, data=await self.spotify_http_client.get_playlist(spotify_id))
                        search_tracks = await results.get_all_tracks()
                    except:
                        return await ctx.send("I was not able to find this playlist! Please try again or use a different link.")

                elif search_type == "album":
                    try:
                        results = await self.spotify_client.get_album(spotify_id=spotify_id)
                        search_tracks = await results.get_all_tracks()
                    except:
                        return await ctx.send("I was not able to find this album! Please try again or use a different link.")

                elif search_type == 'track':
                    try:
                        results = await self.spotify_client.get_track(spotify_id=spotify_id)
                        search_tracks = [results]
                    except:
                        return await ctx.send("I was not able to find this song! Please try again or use a different link.")
                    tracks = await self.bot.wavelink.get_tracks(f'ytsearch:{search_tracks[0].name} - {search_tracks[0].artists[0].name}')
                    print(search_tracks[0].name)
                    if not tracks:
                        return await ctx.send("⚠️ No tracks could be found by the provided link. Make sure, no extra characters were provided in the link, and that the link is to a song or a playlist. ")
                    return await self.single_song(ctx,controller,tracks,position)

                tracks = [
                    wavelink.Track(
                            id_= 'spotify',
                            info={'title': track.name or 'Unknown', 'author': ', '.join(artist.name for artist in track.artists) or 'Unknown',
                                        'length': track.duration or 0, 'identifier': track.id or 'Unknown', 'uri': track.url or 'spotify',
                                        'isStream': False, 'isSeekable': False, 'position': 0, 'thumbnail': track.images[0].url if track.images else None},
                    ) for track in search_tracks
                ]
                if search_type == "playlist":
                    for track in tracks:
                        controller.queue.put_nowait(track)
                    return await ctx.send(f"Queued **{len(tracks)}** tracks")

                elif search_type == "album":
                    for track in tracks:
                        controller.queue.put_nowait(track)
                    return await ctx.send(f"Queued **{len(tracks)}** tracks")

            else:
                tracks = await self.bot.wavelink.get_tracks(query,retry_on_failure = True)

            if not tracks:
                return await ctx.send("⚠️ No tracks could be found by the provided link. Make sure, no extra characters were provided in the link, and that the link is to a song or a playlist. ")

        else:
            tracks = await self.bot.wavelink.get_tracks(f'{source}:{query}')
            if not tracks:
                tracks = await self.bot.wavelink.get_tracks(f'scsearch:{query}')
                if not tracks:
                    return await ctx.send("⚠️ I could not find any results with the provided search query on Youtube or on Soundcloud.")

        if isinstance(tracks, wavelink.TrackPlaylist):
            for track in tracks.tracks:
                track = Track(track.id, track.info, requester=ctx.author, pn= False)
                await controller.queue.put(track)
            await ctx.send(f"```ini\n[Added {len(tracks.tracks)} songs to the Queue.]\n``` ")

        else:
            return await self.single_song(ctx,controller,tracks,position)

    @commands.Cog.listener()
    async def on_command_error(self,ctx,error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send("⚠️ You have to specify something to use this command. For help write '.help'")
        elif isinstance(error, commands.BadArgument):
            return await ctx.message.add_reaction("⚠️")

        elif isinstance(error, commands.CommandNotFound):
            pass

        # elif isinstance(error, commands.CommandInvokeError):
        #     error = error.original
        #     if isinstance(error, discord.Forbidden):
        #         await ctx.send("Missing permissions!")
        else:
            raise error

    @commands.command(name="join",aliases=['connect'])
    async def connect_(self,ctx):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('No channel to join. Please join one.')


        if not hasattr(ctx.me.guild_permissions, "speak"):
            embed= discord.Embed(color= 0x2f3136 ,title="I do not have permissions to speak in the Voice channel!!!")
            return await ctx.send(embed=embed)

        elif not hasattr(ctx.me.guild_permissions, "connect"):
            embed= discord.Embed(color= 0x2f3136 ,title="I do not have permissions to connect to the voice channel!!")
            return await ctx.send(embed=embed)

        player = self.bot.wavelink.get_player(ctx.guild.id)

        await ctx.send(f"Connected to: **{channel.name}**")
        await player.connect(channel.id)
        await ctx.guild.change_voice_state(channel=channel, self_mute=False, self_deaf=True)

        controller = self.get_controller(ctx)
        controller.vc_channel = channel
        controller.channel = ctx.channel


    @commands.command(name= "play",aliases=['p'])
    async def play(self, ctx, *,query: str):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('You can only use this command when you are connected to a voice channel!')

        #player = self.bot.get_player(ctx.guild.id)
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            await ctx.invoke(self.connect_)
        await self.process_request(position= "",ctx= ctx,source="ytsearch",query=query)
        controller = self.get_controller(ctx)
        if not player.is_playing:
            await controller.controller_loop()

    @commands.command(name='playnext',aliases=["pn"])
    async def play_next(self,ctx, *,query: str):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('You can only use this command when you are connected to a voice channel!')

        #player = self.bot.get_player(ctx.guild.id)
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            await ctx.invoke(self.connect_)

        await self.process_request(position= "pn",ctx= ctx,source="ytsearch",query=query)

    @commands.command(name="skip",aliases=['next','forward'])
    async def skip(self,ctx,time:int=None):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('You can only use this command when you are connected to a voice channel!')

        player = self.bot.wavelink.get_player(ctx.guild.id)
        controller = self.get_controller(ctx)

        if not player.is_playing:
            return await ctx.send("No song is currently being played.")

        NoneType = type(None)
        if isinstance(time,NoneType):
            await player.stop()
            await ctx.message.add_reaction("⏭️")

        else:
            new_pos = player.position + (time*1000)
            if new_pos > (player.current.length - player.position):
                await player.stop()
            else:
                await player.seek(new_pos)
                await ctx.invoke(self.now_playing)

    @skip.error
    async def skip_error(self,ctx,error):
        if isinstance(error, commands.BadArgument):
            await ctx.message.add_reaction("⚠️")
        else:
            raise error

    @commands.command(name="rewind",aliases=['back'])
    async def rewind(self,ctx,time:int=None):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('You can only use this command when you are connected to a voice channel!')
        player= self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            return

        if not player.is_playing:
            return await ctx.invoke(self.previous)
        else:
            NoneType = type(None)
            if isinstance(time,NoneType):
                await player.seek()
                return await ctx.message.add_reaction("⏪")

            else:
                new_pos = player.position - (time*1000)
                if new_pos > player.position:
                    await player.seek()
                else:
                    await player.seek(new_pos)
                return await ctx.invoke(self.now_playing)

    @rewind.error
    async def rewind_error(self,ctx,error):
        if isinstance(error, commands.BadArgument):
            await ctx.message.add_reaction("⚠️")
        else:
            raise error

    @commands.command(name="pause",aliases=['wait','stop',"||"])
    async def pause(self,ctx):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('You can only use this command when you are connected to a voice channel!')

        player = self.bot.wavelink.get_player(ctx.guild.id)
        if player.is_paused:
            return

        await player.set_pause(True)
        await ctx.message.add_reaction("⏸️")

    @commands.command(name="resume",aliases=['res','unpause'])
    async def resume(self, ctx):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('You can only use this command when you are connected to a voice channel!')

        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_playing:
            return
        await player.set_pause(False)
        await ctx.message.add_reaction("▶️")

    @commands.command(name="volume",aliases=['vol'])
    async def volume(self, ctx,*,vol: int):
        if not isinstance(vol, int):
            return await ctx.send("You have to eneter an integer for the volume.")

        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('You can only use this command when you are connected to a voice channel!')

        player= self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_playing:
            return
        if not 0 < vol < 101:
             return await ctx.send("The volume you want to set should be between 1-100")

        await player.set_volume(vol)
        await ctx.message.add_reaction("👍")

    @commands.command(name="nowplaying",aliases=['np','current'])
    async def now_playing(self,ctx):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('You can only use this command when you are connected to a voice channel!')

        player= self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_playing:
            return

        controller = self.get_controller(ctx)
        # try:
        #     # Remove our previous now_playing message.
        #     await controller.np.delete()
        # except discord.HTTPException:
        #     pass

        passed = dt.timedelta(milliseconds = player.position)
        rounded = datetime.timedelta(seconds=round(passed.total_seconds()))
        tick_or_not= lambda x: "✔️" if x else "❌"
        upcoming = list(itertools.islice(controller.queue._queue, 0, 1))
        if upcoming:
            fmt = "\n".join(f"[{_.title}]({_.uri}) | `{dt.timedelta(milliseconds = _.length)}`" for _ in upcoming)
        else:
            fmt = "No other songs added to queue."

        num =(player.position/player.current.duration)*100
        loaded_bar= "――――――――――――――――――――"
        load= ""
        for i in range(20):
            # if 0<num<5:
            #     pos= f"\n{controller.duration} **`|•———————————————————|`** {rounded}"
            if i*5<num<(i+1)*5:
                loaded_bar= list(loaded_bar)
                loaded_bar[i]="🟣"
                pos = f"\n{rounded} **`|{load.join(loaded_bar)}|`** {controller.duration}"
                break

        try:
            embed = discord.Embed(title= f"{player.current.title}", url = f"{player.current.uri}",
            description = pos,color= discord.Color.from_rgb(132,112,255))
        except AttributeError:
            return

        #temporary thing
        if hasattr(player.current,"requester"):
            embed.set_author(name = f"Now Playing \nRequested by: {player.current.requester}")

        if player.current.thumb:
            embed.set_thumbnail(url=f"{player.current.thumb}")
        embed.add_field(name= "Volume",value= f"{player.volume}",inline= True)
        embed.add_field(name= "Queue",value= f"{controller.queue.qsize()}")
        embed.add_field(name = "Coming up next:", value= f'{fmt}', inline = False)
        # embed.set_footer(text= f"• Queue Loop: **{controller.loop_queue}** | Track Loop: **{controller.loop_track}**\n Type .np for an updated now playing message.")
        embed.set_footer(text= f"• Queue Loop: {tick_or_not(controller.loop_queue)} | Track Loop: {tick_or_not(controller.loop_track)} | Paused: {tick_or_not(player.is_paused)}\n Type .np for an updated now playing message.")
        controller.np = await ctx.send(embed = embed)

    @commands.command(name="queue",aliases=['q','playlist'])
    async def queue(self,ctx):
        controller = self.get_controller(ctx)
        #
        # fmt = "\n".join(f"{i}. [{v}]({v.uri}) | `{dt.timedelta(milliseconds = v.length)}`\n" for i,v in enumerate(controller.queue._queue, start=1))
        # embed = discord.Embed(title=f"Upcoming- {controller.queue.qsize()}",description=fmt,
        # color= discord.Color.from_rgb(132,112,255))
        pages = menus.MenuPages(source=MySource(list(controller.queue._queue)), clear_reactions_after=True)
        # await ctx.invoke(self.now_playing)
        # await ctx.send(embed=embed)
        await pages.start(ctx)

    @commands.command(name="disconnect",aliases=['leave'])
    async def disconnect(self,ctx):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('You can only use this command when you are connected to a voice channel!')

        controller = self.get_controller(ctx)
        player= self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            return await ctx.send("I am not connected to the vc!")

        if player.is_playing:
            await player.stop()

        await player.destroy()

        try:
            del self.controllers[ctx.guild.id]
        except KeyError:
            pass

    @commands.command(name="shuffle",aliases=['mix'])
    async def shuffle(self, ctx):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('You can only use this command when you are connected to a voice channel!')

        player= self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_playing:
            return

        controller = self.get_controller(ctx)

        if controller.queue.qsize()< 3:
            return await ctx.send("The queue must have 3 or more songs to be shuffled.")

        else:
            await ctx.message.add_reaction("🔀")
            shuffle(controller.queue._queue)
            await ctx.invoke(self.queue)

    @commands.command()
    async def bass_boost(self,ctx):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('You can only use this command when you are connected to a voice channel!')

        player= self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_playing:
            return

        equaliser = wavelink.Equalizer.boost()
        eq = equaliser.get(equalizer.lower(), None)
        await player.set_eq(equaliser)

    @commands.command(aliases=['eq'])
    async def equalizer(self, ctx: commands.Context, *, equalizer: str):

        player= self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            return

        eqs = {'flat': wavelink.Equalizer.flat(),
               'boost': wavelink.Equalizer.boost(),
               'metal': wavelink.Equalizer.metal(),
               'piano': wavelink.Equalizer.piano()}

        eq = eqs.get(equalizer.lower(), None)

        if not eq:
            joined = "\n".join(eqs.keys())
            return await ctx.send(f'Invalid EQ provided. Valid EQs:\n\n{joined}')

        await ctx.send(f'Successfully changed equalizer to {equalizer}.')
        await player.set_eq(eq)

    def lyrics_embed(self,title,cont):
        embed = discord.Embed(title=f"Lyrics for {title}",description= cont,color=discord.Color.from_rgb(132,112,255))
        return embed

    @commands.command(name= "lyrics",aliases=['lyric'])
    async def lyrics(self,ctx,*,given= None):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('You can only use this command when you are connected to a voice channel!')

        player= self.bot.wavelink.get_player(ctx.guild.id)
        # if not player.is_playing:
        #     return

        controller = self.get_controller(ctx)

        forbid = ("|","(",")","[","]","official","music","video","lyrics","directed by ","cole","bennett","hd","remix","audio","lyric","animated",
        "chord ","& ","best ","soundtrack ","full ","performance ","clean ","dirty ","explicit ","hq ","pa ","parental advisory ","censored ","uncensored ",
        "starring ","tiktok","tribute","karaoke")

        if isinstance(given,str):
            title= given
        else:
            if player.is_playing:
                track = player.current
                title = track.title.lower()
            else:
                return await ctx.send("⚠️ No song is being played in the vc and name for no song was given! ⚠️")

        for char in forbid:
            title = title.replace(char,"")

        await ctx.send(f"🔎 **Searching** for {title}")

        x = title.split("- ",1)
        try:
            artist_name = x[0]
            track_name = x[1]

        except IndexError:
            track_name= x[0]
            song_in= controller.genius.search_song(title=track_name,get_full_info=False)
            NoneType = type(None)
            if isinstance(song_in,NoneType):
                return await ctx.send("NO mathches found. 😔")
            else:
                song= song_in.lyrics

        else:
            try:
                pos =track_name.index('ft.')
            except ValueError:
                pass

            else:
                print(track_name)
                track_name= track_name.replace(track_name[pos:],"")
                print(track_name)

            url = "https://api.lyrics.ovh/v1/"+ artist_name+"/"+track_name
            try:
                response = requests.get(url,timeout=13)

            except requests.exceptions.Timeout:
                song_in= controller.genius.search_song(title=track_name,artist=artist_name,get_full_info=False)
                NoneType = type(None)

                if isinstance(song_in,NoneType):
                    return await ctx.send("NO mathches found. 😔")

                else:
                    song= song_in.lyrics
            else:
                try:
                    json_data = json.loads(response.text)
                    print(track_name , artist_name)
                    song = json_data['lyrics']
                except:
                    print(track_name)
                    print(artist_name)
                    song_in= controller.genius.search_song(title=track_name,artist=artist_name,get_full_info=False)
                    NoneType = type(None)

                    if isinstance(song_in,NoneType):
                        return await ctx.send("NO mathches found. 😔")

                    else:
                        song= song_in.lyrics

        if len(song) < 2047:
            embed = self.lyrics_embed(title,song)
            return await ctx.send(embed = embed)
        # await ctx.send(f"**Lyrics for {title}**\n{song.lyrics}")
        else:
            emb_count = ceil(len(song)/2047)
            e = len(song)//emb_count
            a_num = -1
            for i in range(1,emb_count+1):
                a_num += 1
                if i == 1:
                    some_var= song[0:e*i+1]
                    embed = discord.Embed(title= f"Lyrics for {title}",description= some_var,color=discord.Color.from_rgb(132,112,255))
                    await ctx.send(embed= embed)
                else:
                    some_var = song[(len(some_var)*a_num):e*i+1]
                    new_embed = discord.Embed(description = some_var,color =discord.Color.from_rgb(132,112,255))
                    await ctx.send(embed = new_embed)

                return

    @commands.command(name="findsong", aliases=["getsong"])
    async def search_lyrics(self,ctx,*,query:str):
        some_dict= {}
        controller = self.get_controller(ctx)
        name= controller.genius.search_lyrics(query)
        iter=itertools.islice(name['sections'][0]['hits'],0,5)
        if not iter:
            fmt = None
        else:
            for i in iter:
                some_dict[i['result']['title']]= i['result']['primary_artist']['name']

            fmt= "\n".join(f"{v} by {some_dict[v]}" for v in some_dict)
        embed = discord.Embed(title="Songs I found:",description= fmt, color = discord.Color.from_rgb(132,112,255))
        embed.set_footer(text = "Not the songs you were looking for? Try searching with some other set of lyrics.")
        await ctx.send(embed=embed)

        if fmt:
            values= some_dict.values()
            keys= some_dict.keys()
            val_list= list(values)
            key_list= list(keys)
            check_msg = await ctx.send("Would you like me to play the first result? `(yes/no)`")
            def check(m):
                return (m.content =="yes" or m.content =="no") and m.channel == ctx.channel and m.author == ctx.author
            try:
                m = await self.bot.wait_for('message',timeout=60.0, check = check)

            except asyncio.TimeoutError:
                await check_msg.delete()

            else:
                if m.content == "yes":
                    player = self.bot.wavelink.get_player(ctx.guild.id)
                    if not player.is_connected:
                        track= list(iter)
                        if not player.is_connected:
                            await ctx.invoke(self.connect_)
                        else:
                            await self.process_request(position="idk", ctx=ctx ,source="ytsearch", query= f"{val_list[0]} by {key_list[0]}")
                elif m.content == "no":
                    await m.add_reaction("👍")
        else:
            return

    @commands.command(name= "loopqueue", aliases=['loopq','lq'])
    async def loop_queue(self,ctx):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('You can only use this command when you are connected to a voice channel!')
        player= self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            return

        controller = self.get_controller(ctx)
        def check(m):
            return (m.content =="yes" or m.content =="no") and m.channel == ctx.channel and m.author == ctx.author

        if controller.loop_queue:
            controller.loop_queue = False
            #self.empty_queue(controller.queue)
            await ctx.send("**`Exiting Loop`**")
            await ctx.invoke(self.queue)

        else:
            if controller.loop_track:
                check_msg = await ctx.send("The Track is already looping, would you like to stop the Track loop and loop this Queue?`(yes/no)`")
                try:
                    m = await self.bot.wait_for('message',timeout=60.0, check = check)
                except asyncio.TimeoutError:
                    await check_msg.delete()

                else:
                    if m.content== "yes":
                        controller.loop_track= False
                        controller.loop_queue= True
                        await controller.queue.put(player.current)
                        return await ctx.send("**Looping Queue.**")
                    elif m.content== "no":
                        return await m.add_reaction("👍")
            else:
                controller.loop_queue= True
                await controller.queue.put(player.current)
                return await ctx.message.add_reaction("🔁")

    @commands.command(name= "looptrack", aliases=['loopsong','ls'])
    async def loop_track(self,ctx):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('You can only use this command when you are connected to a voice channel!')
        player= self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            return
        controller = self.get_controller(ctx)
        def check(m):
            return (m.content =="yes" or m.content =="no") and m.channel == ctx.channel and m.author == ctx.author

        if controller.loop_track:
            controller.loop_track= False
            return await ctx.send("**`Exiting Track loop.`**")

        else:
            if controller.loop_queue:
                check_msg = await ctx.send("The Queue is already looping, would you like to stop the Queue loop and loop this song?`(yes/no)`")
                try:
                    m = await self.bot.wait_for('message',timeout=60.0, check = check)
                except asyncio.TimeoutError:
                    await check_msg.delete()
                else:
                    if m.content== "yes":
                        controller.loop_queue= False
                        controller.loop_track= True
                        await ctx.channel.send("**Looping Track.**")
                    elif m.content== "no":
                        await m.add_reaction("👍")
            else:
                controller.loop_track = True
                return await ctx.message.add_reaction("🔄")

    @commands.command(name= "clearqueue", aliases=['clearq'])
    async def clear_queue(self,ctx):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('You can only use this command when you are connected to a voice channel!')
        player= self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            return
        controller = self.get_controller(ctx)
        if controller.queue.empty():
            await ctx.send("There are no songs added to Queue.")
        else:
            await ctx.message.add_reaction("👍")
            self.empty_queue(controller.queue)

    # @commands.command()
    # async def oops(self,ctx):
    #     try:
    #         channel = ctx.author.voice.channel
    #     except AttributeError:
    #         return await ctx.send('You can only use this command when you are connected to a voice channel!')
    #     player= self.bot.wavelink.get_player(ctx.guild.id)
    #     if not player.is_connected:
    #         return
    #     controller = self.get_controller(ctx)
    #     try:
    #         if controller.queue._queue[0].pn:
    #             controller.queue.get_nowait()
    #             controller.queue.task_done()
    #         else:
    #             await controller.queue._get_right()
    #             controller.queue.task_done()
    #     except IndexError:
    #         await ctx.message.add_reaction("⚠️")
    #     else:
    #         await ctx.message.add_reaction("👍")

    @commands.command(aliases=['prev'])
    async def previous(self,ctx):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('You can only use this command when you are connected to a voice channel!')
        player= self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            return
        controller = self.get_controller(ctx)

        if controller.finished.empty():
            await ctx.send("There are no previous songs!")
        else:
            await ctx.message.add_reaction("⏮️")
            if not player.is_playing:
                song = await controller.finished.get_right()
                await controller.queue.put_left(song)
            else:
                controller.queue._put_left(player.current)
                controller.prev_loop= True
                await player.stop()

    @commands.command(name="put",aliases=["change","insert"])
    async def put(self,ctx,get_pos: int,put_pos):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('You can only use this command when you are connected to a voice channel!')
        player= self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            return

        controller= self.get_controller(ctx)

        if controller.queue.empty():
            return await ctx.send("The Queue is already empty!!")
        try:
            song = controller.queue._queue[get_pos -1]
        except IndexError:
            return await ctx.send(f"The Queue doesn't even have {get_pos} songs in it!!")
        else:
            # for i in range(controller.queue.qsize()):
            #     if i == (get_pos -1):
            #         controller.queue.get_nowait()
            #         controller.queue.task_done()
            #         print(i)
            #         break
            controller.queue.remove(controller.queue._queue[get_pos -1])

            if put_pos == "last":
                await controller.queue.put(song)
            elif put_pos == "first":
                controller.queue._put_left(song)
            else:
                try:
                    controller.queue.insert(int(put_pos)-1,song)
                except ValueError:
                    return await ctx.send("You have to specify the queue position of the song ex `2` or to specify the first and last songs you can say `first` `last`\n ```\n.put 4 last\n```")
                else:
                    return await ctx.message.add_reaction("👍")

    @put.error
    async def put_error(self,ctx,error):
        if isinstance(error, commands.BadArgument) or isinstance(error,commands.MissingRequiredArgument):
            return await ctx.send("⚠️ You can use this command to change the position of a song in the queue.\n `Ex: .put <position of the song in queue> <position you want to change it to>`")
        else:
            raise error

    @commands.command(name="remove",alieas=['r'])
    async def remove(self, ctx, pos="next"):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('You can only use this command when you are connected to a voice channel!')

        player= self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            return

        controller= self.get_controller(ctx)
        if controller.queue.empty():
            return await ctx.send("The Queue is already empty!!")

        if pos == "next" or pos == "first":
            await controller.queue.get()
            controller.queue.task_done()
        elif pos == "last":
            controller.queue.remove(controller.queue._queue[-1])
        else:
            try:
                controller.queue.remove(controller.queue._queue[int(pos) -1])
            except ValueError:
                return await ctx.send("You have to specify the queue position of the song ex `2` or to specify the next and last song you can say `next` `last`\n ```\n.remove next\n```")
            except IndexError:
                return await ctx.send("There aren't even that many songs in the queue. Stop trynna break me!!\n`.q`")

        return await ctx.message.add_reaction("👍")

    @commands.command()
    @commands.is_owner()
    async def controllers(self,ctx):
        await ctx.send(len(self.controllers))

    @commands.command()
    @commands.is_owner()
    async def controllers_info(self,ctx):
        ...

def setup(client):
    client.add_cog(Music(client))
