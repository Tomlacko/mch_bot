import discord
from discord.ext import commands

import asyncio


class FunCommands(commands.Cog):
    """Random joke commands for having fun"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.spampinging = False


    @commands.command(name="spamping")
    async def spamping(self, ctx: commands.Context, user: discord.User, amount: int = 3, delay: int = 2):
        """Pings the targeted user multiple times."""
        
        if await self.bot.is_owner(ctx.author):
            amount = max(min(amount, 20), 1)
            delay = max(min(delay, 60), 1)
            for i in range(amount):
                await ctx.send(f"{user.mention} 🏓")
                await asyncio.sleep(delay)
        else:
            if self.spampinging:
                await ctx.reply("Wait until the previous spampinging finishes...", mention_author=False)
                return
            self.spampinging = True
            amount = max(min(amount, 5), 1)
            delay = max(min(delay, 5), 1)
            for i in range(amount):
                await ctx.send(f"{ctx.author.mention} {'🏓' if ctx.author==user else 'no u'}")
                await asyncio.sleep(delay)
            self.spampinging = False
    
    @spamping.error
    async def spampingError(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.reply(f"Command failed.\nUse `{self.bot.config.bot_prefix}spamping <user> [amount (default=3, min=1, max=5)] [delay (default=2, min=1, max=5)]`.", mention_author=False)






def setup(bot: commands.Bot):
    bot.add_cog(FunCommands(bot))