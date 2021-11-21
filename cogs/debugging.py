import discord
from discord.ext import commands




class Debugging(commands.Cog):
    """Random stuff used during debugging."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.command(name="test")
    @commands.is_owner()
    async def test(self, ctx: commands.Context):
        """Test some code..."""
        #-------------

        if ctx.message.attachment_count > 0:
            att = ctx.message.attachments[0]
            print(att.content_type)
            print(att.url)
            #att.to_file()
        else:
            print("no attachments")


        #-------------
        print("Ran debug function successfully!")
        await ctx.message.add_reaction("✅")
        
    @test.error
    async def testError(self, ctx: commands.Context, error: commands.CommandError):
        print("Debugging failed! Error:")
        print(error)
        await ctx.message.add_reaction("❌")

def setup(bot: commands.Bot):
    bot.add_cog(Debugging(bot))