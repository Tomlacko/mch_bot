import discord
from discord.ext import commands

from time import time

# pylint: disable=import-error
from utils.color_converter import Autocolor
# pylint: disable=import-error
from utils.time_duration_converter import TimeDurationSeconds

from utils import commonutils



class UtilCommands(commands.Cog):
    """Random commands that can come in handy"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    

    @commands.command(name="color")
    async def showColor(self, ctx: commands.Context, *, color: Autocolor):
        """Preview the entered color."""
        #color is an int
        r = color // 65536
        g = (color // 256) % 256
        b = color % 256
        
        hr = format(r, 'x').rjust(2, "0")
        hg = format(g, 'x').rjust(2, "0")
        hb = format(b, 'x').rjust(2, "0")

        hexcolor = (hr+hg+hb).upper()

        embed = discord.Embed(title=f"#{hexcolor}", description=f"({r}, {g}, {b})", color=color)
        embed.set_image(url=f"https://singlecolorimage.com/get/{hexcolor}/200x100")
        embed.set_footer(text=f"{str(color)} / 16777215")
        await ctx.send(embed=embed)
    
    @showColor.error
    async def showColorError(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send("Color not recognized!")
    
    
    @commands.command(name="time")
    async def getTimestamp(self, ctx: commands.Context, duration: TimeDurationSeconds = 0):
        """Adds the (optional) duration to the current time, creating a timestamp."""
        stamp = round(time()) + duration
        await ctx.send(f"Raw timestamp in seconds: `{stamp}`\nFull date: <t:{stamp}:F>\n(<t:{stamp}:R>)")
    @getTimestamp.error
    async def getTimestampError(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send("Invalid format.")

    @commands.command(name="snowflake")
    async def snowflakeToTime(self, ctx: commands.Context, sn: int = 0):
        """Converts a snowflake into a timestamp."""
        if sn<1:
            await ctx.send("Invalid snowflake")
            return
        
        snowtime = commonutils.snowflakeToTime(sn)
        await ctx.send(f"Snowflake timestamp: {snowtime}\n(<t:{snowtime}:F>)")
        




def setup(bot: commands.Bot):
    bot.add_cog(UtilCommands(bot))