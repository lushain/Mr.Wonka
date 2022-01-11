import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, CheckFailure


class Moderator_commands(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def clear(self, ctx, ammount=2):
        channel = ctx.channel
        await channel.purge(limit=ammount)

    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="⚠️",
                description='"The no. of messages you want to delete should be a numerical no."',
                color=discord.Color.gold(),
            )
            await ctx.send(embed=embed)

    @commands.command()
    @has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, *, reason=None):

        role = discord.utils.get(member.guild.roles, name="Muted")
        if not role:
            muted_role = await ctx.guild.create_role(
                name="Muted", color=discord.Color.greyple()
            )
            for channel in ctx.guild.channels:
                await channel.set_permissionmuted(Muted, send_messages=False)

        else:
            pass

        await member.add_roles(role)
        react = "👍"
        await ctx.message.add_reaction(react)
        # await member.edit(mute = True)
        channel = await member.create_dm()
        embed = discord.Embed(
            title="You Have Been Muted!!",
            description=f"You have been muted by {ctx.author.mention} from {member.guild.name} \nReason: {reason}",
            colour=discord.Colour.dark_grey(),
        )
        embed.set_author(name=f"{ctx.author.name}", icon_url=ctx.author.avatar_url)
        await channel.send(embed=embed)

    @commands.command()
    @has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        member.remove_roles(discord.utils.get(ctx.guild.roles, name="Muted"))
        ctx.message.add_reaction("👍")
        channael = await member.create_dm()
        embed = discord.Embed(
            title="congratulations!!",
            discription=f"You have been unmuted from {member.guild.name}!!",
            color=discord.Color.red(),
        )
        channel.send(embed=embed)

    @commands.command()
    @has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        members = ctx.guild.members
        if ctx.author == member:
            embed = discord.Embed(
                title="⚠️",
                discription=f"you cant ban yourself!!",
                color=discord.Color.gold(),
            )

        elif member not in members:
            await ctx.send(f"Member is not even in the server")

        else:
            await member.ban(reason=reason)
            channel = await member.create_dm()
            await ctx.message.add_reaction("👍")
            embed = discord.Embed(
                title="**You Have Been Banned!!**",
                description=f"You have been banned by {ctx.author.mention} from {member.guild.name} \nReason: {reason}",
                colour=discord.Colour.dark_grey(),
            )
            embed.set_author(
                name=f"{ctx.author.name}", icon_url=f"{ctx.author.avatar_url}"
            )
            await channel.send(embed=embed)

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="⚠️",
                description=f"{ctx.author.mention}, you have to mention someone to ban them!! \nExample: ```.ban @user reason``` (you can choose whether you want to mention the reason) ",
                color=discord.Color.gold(),
            )
            await ctx.send(embed=embed)

    @commands.command()
    @has_permissions(ban_members=True)
    async def unban(self, ctx, *, member):
        found = "not"
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split("#")

        for banned_user in banned_users:
            user = banned_user.user
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.message.add_reaction("👍")
                found = "found"

        if found == "not":
            embed = discord.Embed(
                title="**Member not fount!!**⚠️",
                discription="The member was not found, please make sure that the member is still banned. \nSyntax: ```.ban UserName#disciminator```",
                color=discord.Color.gold(),
            )

    @commands.command()
    @has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        members = ctx.guild.members

        if ctx.author == member:
            ctx.message.add_reaction("⚠️")

        elif member not in members:
            await ctx.send(f"Member is not even in the server")

        else:
            await member.kick(reason=reason)
            channel = await member.create_dm()
            embed = discord.Embed(
                title="**You've been kicked!!**",
                discription=f"You were kicked out of {ctx.message.guild} \nby: {ctx.author.name} \nReason: {reason}",
                colour=discord.Color.darker_grey(),
            )
            channel.send(embed=embed)


def setup(client):
    client.add_cog(Moderator_commands(client))
