import discord
from discord.ext import commands

from time import time
from hashlib import sha256
import base64

# pylint: disable=import-error
from utils.color_converter import Autocolor
# pylint: disable=import-error
from utils.time_duration_converter import TimeDurationSeconds
from utils.commonutils import snowflakeToTime, textFileAttachment



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
        await ctx.reply(embed=embed, mention_author=False)
    
    @showColor.error
    async def showColorError(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.reply("Command failed - color not recognized!", mention_author=False)
    
    
    @commands.command(name="time")
    async def getTimestamp(self, ctx: commands.Context, duration: TimeDurationSeconds = 0):
        """Adds the (optional) duration to the current time, creating a timestamp."""
        stamp = round(time()) + duration
        await ctx.reply(f"Raw timestamp in seconds: `{stamp}`\nFull date: <t:{stamp}:F>\n(<t:{stamp}:R>)", mention_author=False)
    @getTimestamp.error
    async def getTimestampError(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.reply("Command failed - invalid format.", mention_author=False)

    @commands.command(name="snowflake")
    async def snowflakeToTime(self, ctx: commands.Context, sn: int = 0):
        """Converts a snowflake into a timestamp."""
        if sn<1:
            await ctx.reply("Command failed - invalid snowflake", mention_author=False)
            return
        
        snowtime = snowflakeToTime(sn)
        await ctx.reply(f"Snowflake timestamp: {snowtime}\n(<t:{snowtime}:F>)", mention_author=False)
    
    @commands.command(name="sha256", aliases=["hash"])
    async def sha256Command(self, ctx: commands.Context, *, text: str = ""):
        """Converts the given text into a sha256 hash"""
        result = sha256(text.encode("utf-8"))
        await ctx.reply(f"**Hex:** `{result.hexdigest()}`\n**Base64:** `{base64.b64encode(result.digest()).decode('utf-8')}`", mention_author=False)
    
    @commands.command(name="msgSource", aliases=["msgsource", "msgsrc", "msgSrc"])
    async def msgSource(self, ctx: commands.Context, msg: discord.Message = None):
        """Replies with the raw contents of a message uploaded in a file."""
        
        if not msg:
            if ctx.message.reference:
                msg = ctx.message.reference.resolved
            else:
                await ctx.reply("Command failed - no message provided.\nEither reply to a target message with the command, or provide a link to it as an argument.", mention_author=False)
                return
        
        if not msg.type == discord.MessageType.default and not msg.type == 19: #19==replies
            await ctx.reply("Command failed - invalid message type.", mention_author=False)
            return
        
        hasDestinationPerms = False
        if isinstance(msg.channel, discord.DMChannel):
            if msg.channel.recipient != ctx.author:
                await ctx.reply(f"Command failed - you do not have permission to read messages in others' DMs!", mention_author=False)
                return
            hasDestinationPerms = True
        else:
            if msg.channel.guild != ctx.guild:
                otherGuildMember = msg.channel.guild.get_member(ctx.author.id)
                if not otherGuildMember or not self.bot.permhelper.isUserAbove(otherGuildMember, 50):
                    await ctx.reply(f"Command failed - you do not have permission to run this command for that server!", mention_author=False)
                    return
                perms = msg.channel.permissions_for(otherGuildMember)
                if perms.read_messages and perms.read_message_history:
                    hasDestinationPerms = True
            else:
                perms = msg.channel.permissions_for(ctx.author)
                if perms.read_messages and perms.read_message_history:
                    hasDestinationPerms = True

        if isinstance(ctx.channel, discord.TextChannel) and not self.bot.permhelper.isUserAbove(ctx.author, 50):
            await ctx.reply(f"Command failed - you don't have permission to run this command in this server.\nThis command requires permission level {50}, while your level is only {self.bot.permhelper.getUserPermLevel(ctx.author)}.", mention_author=False)
            return
            
        if not hasDestinationPerms:
            await ctx.reply("Command failed - you do not have permission to read messages in that channel!", mention_author=False)
            return

        await ctx.reply(
            file=textFileAttachment(f"msgsrc_{'dm' if isinstance(msg.channel, discord.DMChannel) else msg.channel.guild.id}_{msg.channel.id}_{msg.id}.txt", msg.content),
            mention_author=False
        )
    
    @msgSource.error
    async def msgSourceError(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MessageNotFound):
            await ctx.reply("Command failed - message not found.\nTry using a full URL link instead, or simply reply to the message.", mention_author=False)
        else:
            await ctx.reply(f"Command failed.\n`{error.__class__.__name__}: {error}`", mention_author=False)




def setup(bot: commands.Bot):
    bot.add_cog(UtilCommands(bot))