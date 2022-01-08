import discord
from discord.ext import commands


class EmbedCreator(commands.Cog):
    """Let's you use the bot to create an embed"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="simpleEmbed")
    async def makeSimpleEmbed(self, ctx: commands.Context, title: str, text: str):
        """Create a simple embed using the bot."""
        embed = discord.Embed(title=title, description=text, color=0x0055BB)
        await ctx.send(embed=embed)
    
    @makeSimpleEmbed.error
    async def makeSimpleEmbedError(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send(f"Failed to create embed.\n`{error.__class__.__name__}: {error}`")
        



def setup(bot: commands.Bot):
    bot.add_cog(EmbedCreator(bot))