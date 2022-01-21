import discord
from discord.ext import commands
from time import time

from utils import commonutils


threshold = 24 * 3600 * 7 #1 week


class NewAccountsAlerts(commands.Cog):
    """Send an alert when a freshly created user account joins."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        acc_timestamp = commonutils.snowflakeToTime(member.id)
        acc_age = round(time()-acc_timestamp)

        if acc_age < threshold:
            s = acc_age % 60
            m = (acc_age // 60) % 60
            h = (acc_age // 3600) % 24
            d = (acc_age // 86400) % 7

            alert_channel = self.bot.get_channel(self.bot.config.alert_channel_id)
            await alert_channel.send(f"NEW USER: {member.mention} ({member.id}) was created in the last week, on <t:{acc_timestamp}:F> ({d}d {h}h {m}m {s}s ago).")#, allowed_mentions=discord.AllowedMentions.none()) #must ping, otherwise doesn't show usernames
        



def setup(bot: commands.Bot):
    bot.add_cog(NewAccountsAlerts(bot))