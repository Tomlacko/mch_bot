import discord
from discord.ext import commands

import time


class TestCommands(commands.Cog):
    """Basic commands intended mostly for testing."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Test the response time."""
        start_time = time.time()
        message:discord.Message = await ctx.send("Measuring ping...")
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
        await ctx.send(text)






def setup(bot: commands.Bot):
    bot.add_cog(TestCommands(bot))