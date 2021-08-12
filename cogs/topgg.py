import topgg
import discord
from discord.ext import commands

class Post(commands.Cog):

    def __init__(self,bot):
        self.bot = bot

        dbl_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjgzNTM3MzEyMjk3ODU3ODQ2MyIsImJvdCI6dHJ1ZSwiaWF0IjoxNjI0NDM3MjU5fQ.AXZkiqGY8QUHdERjInmiYolPnKfouWQCGUJ4tk3Bm3c"  # set this to your bot's Top.gg token
        self.bot.topggpy = topgg.DBLClient(bot, dbl_token, autopost=True, post_shard_count=True)

        @commands.Cog.listener()
        async def on_autopost_success():
            print(f"Posted server count ({self.bot.topggpy.guild_count}), shard count ({self.bot.shard_count})")

def setup(client):
    client.add_cog(Post(client))
