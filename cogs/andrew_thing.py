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
        self.last_triggered_when = None


    @commands.Cog.listener()
    async def on_typing(self, channel, user, when: datetime):
        if user.id != andrewID:
            return
        
        #cooldown to prevent triggering itself repeatedly
        if self.last_triggered_when and self.last_triggered_when > when-timedelta(hours=1):
            return

        #reset progress if no further typing was done for a while
        if self.last_typing_when and self.last_typing_when < when-timedelta(minutes=20):
            self.typing_attempts = 0
            self.unsent_messages = 0

        #update values with new ones
        self.last_channel = channel
        self.last_typing_when = when
        self.typing_attempts+=1

        #do not wait for the typing to stop if it's been going on for a long time already
        if self.typing_attempts < 5:
            #keep trying to wait and see when the typing stops
            if self.timer_task:
                self.timer_task.cancel()
            self.timer_task = asyncio.create_task(self.countdown())
    
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.id == andrewID:
            #reset all progress if andrew actually ends up sending a message
            if self.timer_task:
                self.timer_task.cancel()
            self.typing_attempts = 0
            self.unsent_messages = 0
    
    async def countdown(self):
        await asyncio.sleep(30)
        await self.trySayTheThing()

    
    async def trySayTheThing(self):
        #if this function triggers, andrew has stopped typing for a while

        self.typing_attempts = 0
        self.unsent_messages+=1

        #don't trigger the first few times andrew stops tying
        if self.unsent_messages < 3:
            return
        
        #the more andrew "does the thing", the higher the chance of triggering the message
        if random.randint(1, self.unsent_messages) < 3:
            return
        
        #all checks passed, send the thing
        self.unsent_messages = 0
        self.last_triggered_when = datetime.now()
        await self.last_channel.send("Uh oh.. Andrew is doing *the thing* again...")




def setup(bot: commands.Bot):
    bot.add_cog(AndrewThing(bot))