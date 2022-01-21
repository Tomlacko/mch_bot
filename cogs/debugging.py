import discord
from discord.ext import commands

import asyncio


class Debugging(commands.Cog):
    """Random stuff used during debugging."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot



    @commands.command(name="test", hidden=True)
    @commands.is_owner()
    async def test(self, ctx: commands.Context):
        """Test some code..."""
        #-------------

        
        print("Hello world!")


        #-------------
        print("Ran debug function successfully!")
        await ctx.message.add_reaction("✅")
        
    @test.error
    async def testError(self, ctx: commands.Context, error: commands.CommandError):
        print("Debugging failed! Error:")
        print(f"{error.__class__.__name__}: {error}")
        await ctx.message.add_reaction("❌")
    

    @commands.command(name="temp", hidden=True)
    @commands.is_owner()
    async def tempCommand(self, ctx: commands.Context):
        pass



def setup(bot: commands.Bot):
    bot.add_cog(Debugging(bot))