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
        if not msg.guild:
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
            await ctx.reply(f"Message sent! Any replies will be posted in this channel until a bot restart.", mention_author=False)
        
        self.activeDMs[user.id] = ctx.channel
        await ctx.message.add_reaction("✅")
    @dmCommand.error
    async def dmCommandError(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.reply(f"Command failed.\n`{error}`", mention_author=False)
        
        


def setup(bot: commands.Bot):
    bot.add_cog(Modmail(bot))