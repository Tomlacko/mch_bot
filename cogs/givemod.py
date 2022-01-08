import discord
from discord.ext import commands

import asyncio
from time import time


from utils.simpledb import SimpleDB




staff_role_id = 766054073157419008
duration = 100 #100 seconds


class GiveMod(commands.Cog):
    """Give yourself the staff role (as a joke)"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = SimpleDB(self.bot.globaldata["dbdir"], "givemod")
        self.loaded = False
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Reload given staff roles"""

        if self.loaded:
            return
        self.loaded = True

        data = await self.db.getData()
        for guild_id, guild_data in data.items():
            guild = self.bot.get_guild(int(guild_id))
            for user_id, end_timestamp in guild_data.items():
                member = guild.get_member(int(user_id))
                asyncio.create_task(self.unmodAt(member, end_timestamp))

    @commands.guild_only()
    @commands.command(name="givemod")
    async def givemod(self, ctx: commands.Context, member: discord.Member = None):
        """Gives the staff role to the user for some time."""
        
        author = ctx.message.author
        targetUser = author if member is None else member
        staff_role = discord.utils.get(ctx.guild.roles, id=staff_role_id)
        
        if staff_role in targetUser.roles:
            await ctx.reply(f"B-but.. {'u' if member is None else 'they'} already are.. mod? 😟", mention_author=False)
        else:
            end_timestamp = round(time()) + duration

            data = await self.db.getData()
            g = data.setdefault(str(ctx.message.guild.id), {})
            g[str(targetUser.id)] = end_timestamp
            await self.db.saveData(data)

            await targetUser.add_roles(staff_role, reason="givemod joke command", atomic=True)
            await ctx.reply(f"Ok.. {'you' if member is None else 'they'} are now a mod.. I guess... 🤷", mention_author=False)
            
            await self.unmodAt(targetUser, end_timestamp)
    
    @givemod.error
    async def givemodError(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.reply("This command can only be run in a server.", mention_author=False)
        elif isinstance(error, commands.BadArgument) or isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.ConversionError):
            await ctx.reply(f"Command failed - bad formatting.", mention_author=False)
        else:
            await ctx.reply(f"Command failed.\n`{error.__class__.__name__}: {error}`", mention_author=False)

    async def unmodAt(self, member: discord.Member, end_timestamp):
        duration = end_timestamp - round(time())
        if duration>0:
            await asyncio.sleep(duration)
        await self.unmod(member)

    async def unmod(self, member: discord.Member):
        data = await self.db.getData()
        data.setdefault(str(member.guild.id), {}).pop(str(member.id), None)
        await self.db.saveData(data)

        staff_role = discord.utils.get(member.guild.roles, id=staff_role_id)
        await member.remove_roles(staff_role, reason="givemod joke expired", atomic=True)
    


def setup(bot: commands.Bot):
    bot.add_cog(GiveMod(bot))