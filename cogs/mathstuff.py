import discord
from discord.ext import commands

import random



class MathStuff(commands.Cog):
    """Math-related commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    

    @commands.command(name="math")
    async def mathCommand(self, ctx: commands.Context, *, expression: str = ""):
        """[TODO] Evaluates a mathematical expression."""
        #https://stackoverflow.com/questions/2371436/evaluating-a-mathematical-expression-in-a-string
        await ctx.reply("Not implemented yet, coming soon! (hopefully).", mention_author=False)

    @mathCommand.error
    async def mathCommandError(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.reply("Command failed.", mention_author=False)




    @commands.command(name="random", aliases=["randomchoice", "randombool"])
    async def randomChoice(self, ctx: commands.Context, *choices: str):
        """Chooses one of the arguments randomly"""
        if not choices:
            choices = ("No", "Yes")
        if len(choices)==1:
            await ctx.reply(f"After some extremely randomized choosing from the one singular option that was given to choose from, the surprising result is:\n{choices[0]}", mention_author=False)
        else:
            await ctx.reply(f"Randomly chosen result:\n{random.choice(choices)}", mention_author=False)
    
    @commands.command(name="randomint", aliases=["randomnum"])
    async def randomInt(self, ctx: commands.Context, start: int = None, stop: int = None):
        """Chooses a random whole number from a range (inclusive)"""
        if not start:
            start = 0
            stop = 1
        elif not stop:
            stop = start
            start = 0
        if start>stop:
            temp = start
            start = stop
            stop = temp
        await ctx.reply(str(random.randint(start, stop)), mention_author=False)
    @randomInt.error
    async def randomIntError(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.reply(f"Command failed.\nUse `{self.bot.config.bot_prefix}randomint [minimum (default=0)] [maximum (default=1)]`.\nAlternatively, specifying only one argument will make it choose between it and 0.\n(Ranges are inclusive.)", mention_author=False)
    
    @commands.command(name="randomfloat")
    async def randomFloat(self, ctx: commands.Context, start: float = None, stop: float = None):
        """Chooses a random floating-point number from a range (inclusive)"""
        if not start:
            start = 0.0
            stop = 1.0
        elif not stop:
            stop = start
            start = 0.0
        if start>stop:
            temp = start
            start = stop
            stop = temp
        await ctx.reply(str(random.uniform(start, stop)), mention_author=False)
    @randomFloat.error
    async def randomFloatError(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.reply(f"Command failed.\nUse `{self.bot.config.bot_prefix}randomfloat [minimum (default=0)] [maximum (default=1)]`.\nAlternatively, specifying only one argument will make it choose between it and 0.\n(Ranges are inclusive.)", mention_author=False)




def setup(bot: commands.Bot):
    bot.add_cog(MathStuff(bot))