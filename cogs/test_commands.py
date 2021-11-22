import discord
from discord.ext import commands

import time


class TestCommands(commands.Cog):
    """Basic commands intended mostly for testing."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        #log DMs
        if not msg.guild:
            print(f"\nDM from {msg.author} ({msg.author.id}): {msg.content}")


    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Test the response time."""
        start_time = time.time()
        message = await ctx.reply("Measuring ping...", mention_author=False)
        end_time = time.time()

        api_latency = round((end_time - start_time)*1000)/1000
        websocket_latency = round(self.bot.latency*1000)/1000

        await message.edit(content=f"Pong!\nWebsocket latency: {websocket_latency}s\nAPI latency: {api_latency}s")


    @commands.command(name="say")
    async def say(self, ctx: commands.Context, *, text: str = ""):
        """Repeat what the user says"""
        text = text.strip()
        if text:
            await ctx.send(text)

    @commands.guild_only()
    @commands.command(name="level")
    async def showPermLevel(self, ctx: commands.Context, member: discord.Member = None):
        """Tells you what your (or others') permission level is from the bot's POV"""
        if not member:
            await ctx.reply(f"Your permission level is {self.bot.permhelper.getUserPermLevel(ctx.author)}", mention_author=False)
        else:
            await ctx.reply(f"The permission level of {member.mention} is {self.bot.permhelper.getUserPermLevel(member)}", mention_author=False, allowed_mentions=discord.AllowedMentions.none())
    @showPermLevel.error
    async def showPermLevelError(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.reply("This command can only be run in a server.", mention_author=False)
        else:
            await ctx.reply("Command failed.\nUsage: Enter a member as an argument to check their level, or don't provide any to check yours.", mention_author=False)


    @commands.command(name="cogs")
    async def listCogStatus(self, ctx: commands.Context):
        """Show the list and status of all cogs"""

        botdata = self.bot.globaldata["status"]

        text = f"""__**Cog overview:**__
Total cogs: {botdata['cogs_total']}
Active cogs: **{botdata['cogs_loaded']}**
Disabled cogs: {botdata['cogs_disabled']}
Broken cogs: **{botdata['cogs_failed']}**

__**List of cogs:**__
```
| Cog name                | Status |
--------------------------|---------
"""

        for cogname, cogstatus in botdata["coglist"].items():
            text += cogname.ljust(25, " ") + " - " + cogstatus + "\n"
        
        text += "```"
        await ctx.reply(text, mention_author=False)






def setup(bot: commands.Bot):
    bot.add_cog(TestCommands(bot))