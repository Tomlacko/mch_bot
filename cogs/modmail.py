import discord
from discord.ext import commands



class Modmail(commands.Cog):
    """Commands for DMing with users"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.activeDMs = {}

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        #log DMs
        if not msg.guild and not msg.content.startswith(self.bot.config.bot_prefix):
            relayChannel = self.activeDMs.get(msg.author.id, None)
            if relayChannel:
                await relayChannel.send(
                    f"__DM reply from {msg.author.mention}:__\n{msg.content}",
                    files=[await att.to_file() for att in msg.attachments],
                    allowed_mentions=discord.AllowedMentions.none()
                )


    @commands.command(name="dm")
    async def dmCommand(self, ctx: commands.Context, user: discord.User, *, text: str = ""):
        """DMs the user with the content of your message"""

        ranInDms = not isinstance(ctx.channel, discord.TextChannel)
        if ranInDms and not await self.bot.is_owner(ctx.author):
            await ctx.reply("This command only works in a server.", mention_author=False)
            return
        
        if not (ranInDms or self.bot.permhelper.isUserAbove(ctx.author, 100)):
            await ctx.reply("You do not have permission to run this command!", mention_author=False)
            return

        if not text and not ctx.message.attachments:
            await ctx.reply("Command failed - no content provided.", mention_author=False)
            return
        
        await user.send(text, files=[await att.to_file() for att in ctx.message.attachments])
        
        if not user.id in self.activeDMs:
            await ctx.reply(f"__Message to {user.mention} has been sent!__\nAny replies will be posted in this channel until a bot restart.", mention_author=False, allowed_mentions=discord.AllowedMentions.none())
        
        self.activeDMs[user.id] = ctx.channel
        await ctx.message.add_reaction("✅")
    
    @dmCommand.error
    async def dmCommandError(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.reply(f"Command failed.\n`{error.__class__.__name__}: {error}`", mention_author=False)
    

    @commands.command(name="closedm")
    async def closeDm(self, ctx: commands.Context, user: discord.User = None):
        """Closes the DM link."""

        ranInDms = not isinstance(ctx.channel, discord.TextChannel)

        if not user:
            if ranInDms:
                linkedChannel = self.activeDMs.pop(ctx.author.id, None)
                if not linkedChannel:
                    await ctx.reply(f"Command failed - no active DMs to close.", mention_author=False)
                else:
                    await linkedChannel.send(f"__{ctx.author.mention} closed the DM.__", allowed_mentions=discord.AllowedMentions.none())
                    await ctx.reply(f"The DM link has been successfully closed and your messages will no longer be sent.", mention_author=False)
            else:
                await ctx.reply(f"Command failed - no user was specified.", mention_author=False)
        else:
            linkedChannel = self.activeDMs.pop(user.id, None)
            if not linkedChannel:
                await ctx.reply(f"Command failed - no active DMs to close with that user.", mention_author=False)
            else:
                await ctx.reply(f"DMs with {user.mention} have now been closed.", mention_author=False, allowed_mentions=discord.AllowedMentions.none())
                await user.send("*The moderators have now closed this DM and your messages will no longer be sent.*")
    
    @closeDm.error
    async def closeDmError(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.reply(f"Command failed.\n`{error.__class__.__name__}: {error}`", mention_author=False)





def setup(bot: commands.Bot):
    bot.add_cog(Modmail(bot))