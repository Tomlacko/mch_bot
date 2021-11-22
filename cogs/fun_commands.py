import discord
from discord.ext import commands

import asyncio
from hashlib import sha256


class FunCommands(commands.Cog):
    """Random joke commands for having fun"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.spampingers = []


    @commands.command(name="spamping")
    async def spamping(self, ctx: commands.Context, user: discord.User, amount: int = 3, delay: int = 2):
        """Pings the targeted user multiple times."""
        if ctx.author.id in self.spampingers:
            await ctx.reply("Wait until your previous spampinging finishes!", mention_author=False)
            return
        
        self.spampingers.append(ctx.author.id)
        if isinstance(ctx.channel, discord.DMChannel) or self.bot.permhelper.isUserAbove(ctx.author, 100):
            amount = max(min(amount, 10), 1)
            delay = max(min(delay, 10), 1)
            for i in range(amount):
                await ctx.send(f"{user.mention} 🏓")
                await asyncio.sleep(delay)
        else:
            amount = max(min(amount, 5), 1)
            delay = max(min(delay, 5), 1)
            for i in range(amount):
                await ctx.send(f"{ctx.author.mention} {'🏓' if ctx.author==user else 'no u'}")
                await asyncio.sleep(delay)
        self.spampingers.remove(ctx.author.id)
    
    @spamping.error
    async def spampingError(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.reply(f"Command failed.\nUse `{self.bot.config.bot_prefix}spamping <user> [amount (default=3, min=1, max=5)] [delay (default=2, min=1, max=5)]`.", mention_author=False)
    
    @commands.command(name="answer", aliases=["question"])
    async def randomAnswer(self, ctx: commands.Context, *, question: str = ""):
        """Gives a consistent answer to a yes/no question"""
        if not question:
            await ctx.reply(f"Command failed - no question was asked.\nWrite a question after the command and you'll get a consistent answer.", mention_author=False)
        else:
            options = ["No", "Yes", "Most-likely no", "Most-likely yes", "Unsure", "That is confidential information"]
            result = sha256(' '.join(question.split()).lower().encode("utf-8")).digest()[0]
            answer = options[result%len(options)]
            await ctx.reply(f"{answer}.", mention_author=False)


def setup(bot: commands.Bot):
    bot.add_cog(FunCommands(bot))