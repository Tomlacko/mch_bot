import discord
from discord.ext import commands

import asyncio
import random
from datetime import datetime, timedelta


andrewID = 423564249122471936


class AndrewThing(commands.Cog):
    """When the andrew is typing 😳 😱"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_typing_when = None
        self.typing_attempts = 0
        self.unsent_messages = 0
        self.last_channel = None
        self.timer_task = None


    @commands.Cog.listener()
    async def on_typing(self, channel, user, when: datetime):
        if user.id != andrewID:
            return
        
        if not self.last_typing_when or self.last_typing_when < when-timedelta(minutes=30):
            self.typing_attempts = 0
            self.unsent_messages = 0

        self.last_channel = channel
        self.last_typing_when = when
        self.typing_attempts+=1

        if self.typing_attempts < 5:
            if self.timer_task:
                self.timer_task.cancel()
            self.timer_task = asyncio.create_task(self.countdown())
    
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.id == andrewID:
            if self.timer_task:
                self.timer_task.cancel()
            self.typing_attempts = 0
            self.unsent_messages = 0
    
    async def countdown(self):
        await asyncio.sleep(30)
        await self.trySayTheThing()

    
    async def trySayTheThing(self):
        self.typing_attempts = 0
        self.unsent_messages+=1

        if self.unsent_messages < 3:
            return
        
        if random.randint(1, self.unsent_messages) < 3:
            return
        
        self.unsent_messages = 0
        await self.last_channel.send("Uh oh.. Andrew is doing *the thing* again...")




def setup(bot: commands.Bot):
    bot.add_cog(AndrewThing(bot))