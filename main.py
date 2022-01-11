import discord
from discord.ext import commands
from discord.ext import tasks
from discord.ext import menus
import random
import os
import asyncio
from discord_components import DiscordComponents, Button, ButtonStyle, InteractionType
from discord import AllowedMentions

intents = discord.Intents.default()
intents.members = True

client = commands.Bot(command_prefix = '.',intents=intents,help_command= None,allowed_mentions=None)


class MyMenu(menus.Menu):
    async def send_initial_message(self, ctx, channel):
        return await channel.send(embed=first)

    @menus.button('1️⃣')
    async def on_one(self, payload):
        await self.message.edit(embed= first)
        await self.message.remove_reaction("1️⃣")

    @menus.button('2️⃣')
    async def on_two(self, payload):
        await self.message.edit(embed= second)

    @menus.button('3️⃣')
    async def on_three(self, payload):
        await self.message.edit(embed= third)

    @menus.button('🗑️')
    async def on_stop(self, payload):
        self.stop()
        await self.message.clear_reactions()

@client.event
async def on_ready():
    await client.change_presence(activity = discord.Activity(type=discord.ActivityType.listening, name=".help"))
    print("bot is ready")
    DiscordComponents(client)

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if client.user.mentioned_in(message):
        embed = discord.Embed(title="Hey there!",description="My name is Wonka.\n \nMy command prefix is `'.'` so each time you need my help with playing music or to deal with not obeying members, you know who to call.\n"
        "\nYou can call commands like this:\n `.help`\n \nIt's that simple!! For info on everything I can do type in '.help' in the chat.",
        color=discord.Color.from_rgb(132,112,255))
        embed.add_field(name="Vote and support",value="please vote for this bot [here](https://top.gg/bot/835373122978578463/vote)\n Give us your reviews [here](https://top.gg/bot/835373122978578463)")
        embed.set_thumbnail(url= 'https://i.imgur.com/0YKdMjh.jpg')
        embed.set_footer(text="Thanks for using this bot! 💜")
        try:
            await message.channel.send(embed =embed)
        except:
            pass 

    elif message.content ==".loop":
        await message.channel.send("You have to specify whether you want to `.loopq` or `.loopsong` for more info type '.help'.")

    elif message.content == '.name of the command':
        ...

    elif message.content == "test":

        await message.channel.send(
            "Content",
            components=[
                Button(style=ButtonStyle.blue, label="🎵"),
                Button(style=ButtonStyle.red, label="⚖️"),
            ],
        )

        res = await client.wait_for("button_click")
        if res.channel == message.channel:
            await res.respond(
                type=InteractionType.ChannelMessageWithSource,
                content=f'{res.component.label} clicked'
            )


    return await client.process_commands(message)

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        if filename =="queuing.py":
            pass
        elif filename =="new_music.py":
            pass
        else:
            client.load_extension(f'cogs.{filename[:-3]}')

@client.event
async def on_member_join(member):
    if member.guild.id in (844856727517003818 , 110373943822540800 , 765490568963948545):
        return
    else:
        try:
            channel = await member.create_dm()
            embed = discord.Embed(title =f"Welcome to '{member.guild.name}'!!",
            description=f'''
            Hi, and welcome to {member.guild.name}, we hope you have a great experience with us. Enjoy your stay at {member.guild.name}.
            \n \n If you enjoy this bot and would like similar messages for you server as well, **for free!!** \n
            [Click here to invite this bot to your server](https://discord.com/oauth2/authorize?client_id=835373122978578463&permissions=8&scope=bot)''',
            color=discord.Color.from_rgb(132,112,255))
            embed.set_author(name= f"{member.name}",
            icon_url = member.avatar_url)

            embed.set_footer(text= "Thank you for your time 💜")
            await channel.send(embed = embed)
        except Exception:
            pass
    # channel = client.get_channel(ID)
        # channel = await member.create_dm()

@client.event
async def on_member_remove(member):
    if member.guild.id in (844856727517003818 , 110373943822540800 , 765490568963948545):
        return

    try:
        channel = await member.create_dm()
        embed = discord.Embed(title =f"Leaving so soon?",
        description=f"""
        Hope you join '{member.guild.name}' back soon!!
        """,
        color= discord.Color.red())
        embed.set_author(name= f"{member.name}",
        icon_url = member.avatar_url)
        await channel.send(embed = embed)
    except Exception:
        pass

first = discord.Embed(title="Mr.WONKA ",
description = '''
Here are your music commands.
''', color=discord.Color.from_rgb(132,112,255))
first.set_thumbnail(url = "https://i.imgur.com/0YKdMjh.jpg")
#MUSIC
first.add_field(name= "Music",value ="These commands are used for playing music in your voice chat", inline = False)
first.add_field(name= "'.play'",value= "Use this command and the name of the song you want to play to listen to it in your voice chat. Soundcloud, Youtube music, Spotify playlists are supported.", inline = False)
first.add_field(name= "'.pause'",value= "Use this command to pause the currently playing song.")
first.add_field(name= "'.resume'",value= "Use this command to resume a paused song.", inline = True)
first.add_field(name= "'.skip `<time in seconds>`'", value= "Use this command and specify the number of seconds you wanna skip, if not specified, the entire song will skip.")
first.add_field(name= "'.queue' or '.q'", value= "Use this command to have a look at all your queued songs.", inline = True)
first.add_field(name= "'.nowplaying' or '.np'",value= "Use this command to look at the currently playing song.")
first.add_field(name= "'.disconnect' or 'leave'", value= "Use this command to make the bot leave the voice chat.")
first.set_footer(text= "Page 1/3")

second = discord.Embed(color= discord.Color.from_rgb(132,112,255))
second.set_thumbnail(url = "https://i.imgur.com/0YKdMjh.jpg")
second.add_field(name= "'.playnext' or 'pn'",value="Use this command to play the song your liking next.")
second.add_field(name="'.rewind `<time in seconds>`'",value="Use this command and specify the number of seconds you wanna rewind, if not specified, the entire song will rewind.")
second.add_field(name="'.shuffle'",value="Use this command to shuffle the queued songs.")
second.add_field(name="'.lyrics `<name of artist - name of song>`'",value="This command to get the lyrics of the currently playing song right to your text channel, if a name is specified, you'll get that songs lyrics.")
second.add_field(name="'findsong' or '.getsong'",value="Ever forget the name of some song but remember the lyrics? We've got you covered!")
second.add_field(name="'.previous' or '.prev'",value="Play the last playing song in your vc. You can only use this command for the last 10 songs.")
second.set_footer(text= "Page 2/3")

third = discord.Embed(color= discord.Color.from_rgb(132,112,255))
third.set_thumbnail(url = "https://i.imgur.com/0YKdMjh.jpg")
third.add_field(name="'.loopqueue' or '.lq'",value="Use this command to play the current queue on loop. This is a toggle command, you'll need to call this command again to exit.")
third.add_field(name="'.looptrack' or '.ls'",value="Use this command to play the currently playing song on loop. This is a toggle command, you'll need to call this command again to exit.")
third.add_field(name="'.volume' or '.vol'", value="Use this command to change volume of the player between 1-100.")
third.add_field(name="'.clearqueue' or '.clearq'",value="Use this to clear the queue.")
third.add_field(name="'.change' or '.put' `<pos of song>` `<pos you want to change to>`",value="Use this command to change the pos of a song in the Queue. Type 'last' or 'first' to put the chosen song to fisrt or last.")
third.add_field(name="'.remove' or '.r' `<position>`",value="Use this command to remove the song at the specified Queue position. Use the queue command to get the queue position of each song.")
third.add_field(name="'.privacy'",value="Veiw our privacy policy.")
third.set_footer(text= "Page 3/3")

@client.command(aliases=[])
async def help(ctx):
    embed = discord.Embed(title=client.user.name,url="https://top.gg/bot/835373122978578463",
    description="Glad you asked.",
    color= discord.Color.from_rgb(132,112,255))
    embed.set_thumbnail(url = "https://i.imgur.com/0YKdMjh.jpg")

    embed.add_field(name="Music",value="For the music commands react to the 🎵")
    embed.add_field(name="Moderation",value="For the moderation commands react to the ⚖️")
    embed.add_field(name="Vote and support",value="please vote for this bot [here](https://top.gg/bot/835373122978578463/vote)\n\n Give us your reviews [here](https://top.gg/bot/835373122978578463)")
    embed.add_field(name="Invite", value="Like this bot? Want it in your server?\n"
    "Type **'.invite'**\n This will give you an invite link in the server and you will also get a DM. ;-)", inline=False)
    your_msg = await ctx.send(embed=embed)

    await your_msg.add_reaction("🎵")
    await your_msg.add_reaction("⚖️")

    def check(reaction, user):
        return user== ctx.author and (str(reaction.emoji)== "🎵" or str(reaction.emoji)== "⚖️")

    try:
        reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
        if reaction.emoji == "🎵":
            await your_msg.delete(embed=first)
            m = MyMenu()
            await m.start(ctx)

        elif reaction.emoji == '⚖️':
            await your_msg.delete()
            embed = discord.Embed(title = "Moderation still under construction!",
            description= "Moderation commands will be out soon!!", color=discord.Color.from_rgb(132,112,255))
            await your_msg.send(embed = embed)
    except:
        try:
            await your_msg.clear_reactions()
        except:
            return

@client.command()
async def invite(ctx):
    embed = discord.Embed(title="Thank You for wanting to Invite this bot!!",
    description="**[This is the invite link for the bot](https://discord.com/oauth2/authorize?client_id=835373122978578463&permissions=8&scope=bot)**\n\n"
    "**Help us further develop this bot: [Vote for this bot here](https://top.gg/bot/835373122978578463/vote)**\n\n"
    "**Drop us your reviews on the bot [here](https://top.gg/bot/835373122978578463)**",
    color= discord.Color.from_rgb(132,112,255))
    embed.set_thumbnail(url = "https://i.imgur.com/0YKdMjh.jpg")
    embed.set_footer(text="THANK YOU 💜\n FYI we're always open to suggestions.  :-)")
    await ctx.send(embed= embed)
    try:
        channel = await ctx.author.create_dm()
        await channel.send(embed = embed)
    except:
        pass

@client.command()
async def byebye(ctx):
    goodbye = discord.Embed(title = "This is Goodbye.",
    description = "Mr. Wonka will officially be shut down today, for various reasons we.. I cannot disclose, so, i guess this is goodbye. The bot will be back though, but not anytime soon...",color = discord.Color.from_rgb(132,112,255))
    goodbye.set_footer(text = "Thank you to all those who used this bot\nAnd those who didn't, you missed out (i guess)")
    goodbye.add_field(name="Who am I?", value="Ohh, i'm Lushain#7914 btw.")
    goodbye.set_thumbnail(url= 'https://i.imgur.com/0YKdMjh.jpg')
    await ctx.send(embed = goodbye)

    for i in client.guilds:
        channel = discord.utils.get(i.text_channels, name = "general")
        NoneType = type(None)
        if i.id in (844856727517003818 , 110373943822540800 , 765490568963948545):
            pass

        elif not isinstance(channel,NoneType):
            try:
                await channel.send(embed = goodbye)
            except:
                pass

        else:
            channel = i.system_channel
            try:
                await channel.send(embed = goodbye)
            except:
                pass

@client.command()
async def privacy(ctx):
    embed = discord.Embed(title="Privacy policy",
    description="This bot makes use of the voice channel and text chennels in the server along with the user data to check the roles of the given person in the server. "
    "\nThere is no need to worry about your data being exposed to others since, we keep special care of all user data collected and save only the most essencial data"
    " and only storing the given data whilst the bot is connected to the voice channel.\n\n"
    "Some categories of data we collect are:\nRoles of the users in a given server\nIf a user is connected to the vc or not"
    "\nHow long the user has been connected to the vc",
    color= discord.Color.from_rgb(132,112,255))
    embed.add_field(name="Contact",value="At the moment we don't have any help server (users will be infored when we make one) so, for the moment please contact the Main dev `Lushain#7914` for any help or query.")
    embed.add_field(name="Get data removed",value="To get all the cached data on your ID Direct Message `Lushain#7914` stating why you need your data removed and how we can help. **No applications to get the user data removed will be denied.**")
    embed.add_field(name="Support",value="This is an ever growing bot, we are completly open about the data we collect. \nPlease help further support this bot by inviting it to your own servers.\n`.invite`",inline=False)
    embed.set_footer(text="Made with 💜")
    return await ctx.send(embed = embed)

client.run('ODM1MzczMTIyOTc4NTc4NDYz.YIOf2Q.qmaqXI_iCCJDtiiNWgbj4gsm4tg')
