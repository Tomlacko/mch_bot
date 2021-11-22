import discord
from discord.ext import commands

import asyncio
from time import time

messageText = """
__**Here you can propose new projects!**__

__**BEFORE YOU MAKE A SUGGESTION:**__
:book: **Check if it hasn't been suggested already.** Use Discord's search function, check <#755121689913983136>, pins or ask in <#738860957685776395> if unsure.
:mag_right: **Google it!** A lot of seeds/world downloads are already publicly known!
:thinking: **Consider if what you're suggesting has any significance** to the community, be it historical or technical.
__**HOW TO MAKE A GOOD SUGGESTION:**__
:white_check_mark: Explain properly what you mean and why should we be interested.
:white_check_mark: Try to include a link or an image (where it makes sense).
:x: ***Blatant duplicates and spam will get deleted without notice!** :wastebasket:
Otherwise you'll get notified in <#738860957685776395> if there are any problems.
Repeatedly making bad suggestions will get your access to this channel removed!*
"""

channelID = 738836486199181312 #project-suggestions

remove_reactions_duration = 5*60 #seconds



class BottomMessage(commands.Cog):
    """To keep a message posted at the bottom of a channel."""
    #code adopted from vco's research bot

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.started = False
        self.message = None


    @commands.Cog.listener()
    async def on_ready(self):
        """Get the last self message on startup, if it exists."""
        channel = self.bot.get_channel(channelID)

        success = False
        i = 0
        async for msg in channel.history(limit=100):
            if msg.author == self.bot.user:
                self.message = msg
                success = True
                break
            i += 1

        if success:
            if i>0:
                #delete the old message and send a new one
                await self.message.delete()
                self.message = await channel.send(messageText)
        else:
            #just send a new one
            self.message = await channel.send(messageText)


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != channelID or message.author.bot:
            return

        try:
            await self.message.delete()
        except:
            pass

        self.message = await message.channel.send(messageText)

        check = lambda r, u: r.message == self.message
        stopRemovingReactionsTime = time() + remove_reactions_duration
        
        while time() < stopRemovingReactionsTime:
            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add",
                    check=check,
                    timeout=stopRemovingReactionsTime-time()+1
                )
            except asyncio.TimeoutError:
                pass
            await self.message.clear_reactions()
        



def setup(bot: commands.Bot):
    bot.add_cog(BottomMessage(bot))