import discord
from discord.ext import commands
from time import time

from utils import commonutils


threshold = 24 * 3600 * 7 #1 week
alert_channel = 737298182912082072


class NewAccountsAlerts(commands.Cog):
    """Send an alert when a freshly created user account joins."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return
        
        channel = self.bot.get_channel(alert_channel)
        acc_age = commonutils.snowflakeToTime(member.id)

        if time()-acc_age < threshold:
            s = acc_age % 60
            m = (acc_age // 60) % 60
            h = (acc_age // 3600) % 24
            d = (acc_age // 86400) % 7

            await channel.send(f"NEW USER: {member.mention} ({member.id}) was created in the last week! ({d}d {h}h {m}m {s}s ago)")#, allowed_mentions=discord.AllowedMentions.none()) #must ping, otherwise doesn't show usernames
        



def setup(bot: commands.Bot):
    bot.add_cog(NewAccountsAlerts(bot))