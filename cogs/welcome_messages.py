import discord
from discord.ext import commands


welcome_channel = 824296321036582923 #bot-fun (797053871146926130 = newcomers)


class WelcomeMessages(commands.Cog):
    """Send a message welcoming a user in a given channel"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = self.bot.get_channel(welcome_channel)

        if not channel:
            print("Welcome channel not found!")
            return
        
        await channel.send(f"Member {member.mention} joined", allowed_mentions=discord.AllowedMentions(users=False))



def setup(bot: commands.Bot):
    bot.add_cog(WelcomeMessages(bot))