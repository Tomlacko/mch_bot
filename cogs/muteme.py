import discord
from discord.ext import commands
import asyncio

# pylint: disable=import-error
from utils.time_duration_converter import TimeDurationSeconds
from time import time

from utils.simpledb import SimpleDB

import config


muteme_max_limit = 24*60*60 #1 day


class Muteme(commands.Cog):
    """For muting yourself.. for whatever reason..."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.mutesdb = SimpleDB(self.bot.globaldata["dbdir"], "muteme")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Reload active mutes."""
        data = await self.mutesdb.getData()
        for guild_id, guild_data in data.items():
            guild = self.bot.get_guild(int(guild_id))
            for user_id, end_timestamp in guild_data.items():
                member = guild.get_member(int(user_id))
                asyncio.create_task(self.unmuteAt(member, end_timestamp))

    @commands.command(name="muteme")
    @commands.guild_only()
    async def muteme(self, ctx: commands.Context, duration: TimeDurationSeconds = 60):
        """Mutes the user for the given duration of time."""
        
        author = ctx.message.author
        muted_role = discord.utils.get(ctx.guild.roles, id=config.muted_role_id)
        
        if muted_role in author.roles:
            await ctx.reply("Shut, you are already supposed to be muted 🗿", mention_author=False)
        else:
            duration = max(min(muteme_max_limit, duration), 1)
            end_timestamp = round(time()) + duration

            data = await self.mutesdb.getData()
            g = data.setdefault(str(ctx.message.guild.id), {})
            g[str(author.id)] = end_timestamp
            await self.mutesdb.saveData(data)

            await author.add_roles(muted_role, reason="Used the muteme command.", atomic=True)
            await ctx.reply(f"Muted <@{author.id}> for {duration} seconds. 🗿\n*You will be unmuted <t:{end_timestamp}:R> (<t:{end_timestamp}:F>).*", mention_author=False)
            
            await self.unmuteAt(author, end_timestamp)
    
    @muteme.error
    async def mutemeError(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.BadArgument) or isinstance(error, commands.ConversionError):
            await ctx.reply(f"Command failed - bad formatting.\nUse `{self.bot.config.bot_prefix}muteme [duration (default=1m, min=1s, max=24h)]`, where `duration` has format `yMwdhms`\nExample: `2h15s`.", mention_author=False)
        else:
            await ctx.reply("Command failed.", mention_author=False)

    async def unmuteAt(self, member: discord.Member, end_timestamp):
        duration = end_timestamp - round(time())
        if duration>0:
            await asyncio.sleep(duration)
        await self.unmute(member)

    async def unmute(self, member: discord.Member):
        data = await self.mutesdb.getData()
        data.setdefault(str(member.guild.id), {}).pop(str(member.id), None)
        await self.mutesdb.saveData(data)

        muted_role = discord.utils.get(member.guild.roles, id=config.muted_role_id)
        await member.remove_roles(muted_role, reason="muteme expired.", atomic=True)
    


def setup(bot: commands.Bot):
    bot.add_cog(Muteme(bot))