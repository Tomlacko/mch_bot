import discord
from discord.ext import commands

import asyncio
from collections import deque
from datetime import datetime, timedelta

from utils.commonutils import snowflakeToTime




PROJECT_SUGGESTIONS_ID = 738836486199181312
SUGGESTION_DISCUSSION_ID = 738860957685776395


class ProjectSuggestions(commands.Cog):
    """Manages reactions in #project-suggestions, replies in #suggestion-discussion based on mod reactions, reposts deleted suggestions."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.recently_deleted_suggestions = deque([], 5)
        self.currently_processed_suggestions = deque([], 5)


    @commands.Cog.listener()
    async def on_message_delete(self, msg: discord.Message):
        if msg.channel.id != PROJECT_SUGGESTIONS_ID:
            return

        #remember the last few deleted suggestion message ids
        self.recently_deleted_suggestions.append(msg.id)

    
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.channel.id != PROJECT_SUGGESTIONS_ID or msg.author.bot:
            return
        
        #don't add anything to system messages
        if not msg.type == discord.MessageType.default and not msg.type == 19: #19==replies
            return
        
        #wait until the bottom message gets reposted
        await asyncio.sleep(1)

        #apply reactions to any new suggestion
        for emoji in ["⭐", "downvote:933906083339177995", "🔁", "⏯️", "done:739037536696926239", "🔎", "❓", "⚙️", "💩", "❌", "🚫", "🗑️", "✅"]:
            try:
                #can fail if message gets suddenly deleted
                await msg.add_reaction(emoji)
            except:
                pass
            if msg.id in self.currently_processed_suggestions or msg.id in self.recently_deleted_suggestions:
                break

    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.channel_id != PROJECT_SUGGESTIONS_ID or payload.member.bot:
            return
        
        #do not accidentally trigger an action on an already processed message
        if payload.message_id in self.currently_processed_suggestions or payload.message_id in self.recently_deleted_suggestions:
            return
        
        #fetch the message that has been reacted to
        project_suggestions_channel = self.bot.get_channel(PROJECT_SUGGESTIONS_ID)
        msg: discord.Message = None
        try:
            #this can fail if the message is deleted while a reaction is being applied
            msg = await project_suggestions_channel.fetch_message(payload.message_id)
        except:
            return

        #prevent accidental deletion of older suggestions
        if msg.created_at < datetime.utcnow()-timedelta(weeks=1):
            return

        #removes any reactions from the bottom message
        if msg.author.bot:
            await msg.clear_reactions()
            return
        
        #don't do anything with system messages
        if not msg.type == discord.MessageType.default and not msg.type == 19: #19==replies
            return
        
        #reaction actions are only able to be performed by moderators
        if not self.bot.permhelper.isUserAbove(payload.member, 100):
            if payload.emoji.name not in ["⭐", "downvote"]:
                await msg.remove_reaction(payload.emoji, payload.member)
            return
        
        #construct full emoji identifier
        emoji_str = payload.emoji.name
        if payload.emoji.is_custom_emoji():
            emoji_str += f":{payload.emoji.id}"
        
        #do the appropriate action to the suggestion based on the emoji
        await self.handle_suggestion_reaction(msg, emoji_str)


    async def handle_suggestion_reaction(self, msg: discord.Message, reaction: str):
        special_reactions = ["🔁", "⏯️", "done:739037536696926239", "🔎", "❓", "⚙️", "💩", "❌", "🚫", "🗑️", "✅"]
        if reaction not in special_reactions:
            return
        
        self.currently_processed_suggestions.append(msg.id)

        #approve suggestion
        if reaction == "✅":
            #remove all action-related reactions
            for emoji in reversed(special_reactions):
                try:
                    #can fail if message gets suddenly deleted
                    await msg.clear_reaction(emoji)
                except:
                    pass
                if msg.id in self.recently_deleted_suggestions:
                    break
            try:
                #throws exceptions if not found
                self.currently_processed_suggestions.remove(msg.id)
            except:
                pass
            return

        #reply in #suggestion-discussion and delete the suggestion
        if reaction == "🔁":
            await self.notify_op(msg, "This (or something very similar) has **already been suggested** before.")
        elif reaction == "⏯️":
            await self.notify_op(msg, "**We're already working on this!** Please check <#755121689913983136> to see all our projects.")
        elif reaction == "done:739037536696926239":
           await self.notify_op(msg, "**This has already been done**, either by us, or by someone else. You can check <#755121689913983136> to see all our projects.")
        elif reaction == "🔎":
           await self.notify_op(msg, "What you suggested is **already available to find online!** Try Googling it, or check this list of commonly suggested known seeds: https://discord.com/channels/720723932738486323/738836486199181312/761342951431077889")
        elif reaction == "❓":
            await self.notify_op(msg, "Your suggestion either **doesn't provide enough info, or is unclear / confusing**. Please post it again with more info / clarifications.")
        elif reaction == "⚙️":
            await self.notify_op(msg, "**This isn't something that can be done**, either because you're misunderstanding Minecraft mechanics, or because it just isn't possible for technical reasons, usually because it's too vaguely defined for a program.")
        elif reaction == "💩":
            await self.notify_op(msg, "**Low-quality suggestion** that nobody would be interested in working on.")
        elif reaction == "❌":
            await self.notify_op(msg, "**Suggestion denied** - there are reasons why we won't work on this. Wait for someone to reply with more info...")
        elif reaction == "🚫":
            await self.notify_op(msg, "**This is not a valid suggestion!** You either posted something that is not relevant to Minecraft@Home, or doesn't belong in this channel. If you have any questions or need help, please use <#765713668745854986>.")
        elif reaction == "🗑️":
            await self.notify_op(msg)
        
        await msg.delete()
    

    async def notify_op(self, original_msg: discord.Message, reason: str = ""):
        reply_text = f"__{original_msg.author.mention} Your suggestion in <#{PROJECT_SUGGESTIONS_ID}> has been removed by a moderator.__\n"
        if reason != "":
            reply_text += f"\n__**Reason:**__ {reason}\n"
        reply_text += f"\n*As a general advice, we suggest reading the informational message at the bottom of <#{PROJECT_SUGGESTIONS_ID}>, which contains some info on how to make better suggestions, as well as common reasons why they often get deleted.*\n"
        reply_text += "\nOriginal message:"


        embed = discord.Embed(
            #title="Suggestion:",
            description=original_msg.content,
            color=0xFF0000
        )
        embed.set_author(
            name=f"{original_msg.author.name}#{original_msg.author.discriminator}",
            icon_url=original_msg.author.avatar_url
        )
        timestamp = snowflakeToTime(original_msg.id)
        #embed.set_footer(text=f"Originally posted on <t:{timestamp}:f> (<t:{timestamp}:R>)")
        #footers do not support timestamps, workaround using fields:
        embed.add_field(name="​", value=f"*Originally posted on <t:{timestamp}:f> (<t:{timestamp}:R>)*")

        await self.bot.get_channel(SUGGESTION_DISCUSSION_ID).send(reply_text, embed=embed)

    



def setup(bot: commands.Bot):
    bot.add_cog(ProjectSuggestions(bot))
