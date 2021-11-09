import discord
from discord.ext import commands


from utils.simpledb import SimpleDB


class Debugging(commands.Cog):
    """Random stuff used during debugging."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.command(name="test")
    @commands.is_owner()
    async def test(self, ctx: commands.Context, *, text: str = ""):
        """Test some code..."""


        db = SimpleDB(self.bot.globaldata["dbdir"], "muteme")
        data = await db.getData()
        
        print(data)
        data["key"] = 123
        print(data)

        await db.saveData(data)


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