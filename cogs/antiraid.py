import discord
from discord.ext import commands

import asyncio
from datetime import datetime
from collections import deque

from utils.commonutils import textFileAttachment
from utils.simpledb import SimpleDB



join_queue_length = 5 #the amount of users that have to join quickly after each other to triger the antiraid. (value must be 2 or more)
time_spacing = 4 #seconds #if the spacing between each join is lower than this, then it is considered a raid
raid_end_countdown = 20 #seconds #time that has to pass after the last join to assume that the raid has ended

raidBanMessage = "You have been banned on the Minecraft@Home Discord server for being part of a raid.\nIf this was an accident, appeal here: https://discord.gg/9DwrQpH"



class Antiraid(commands.Cog):
    """Monitors user joins and bans when a raid is detected."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.loaded = False

        self.joins = deque()
        self.all_joins = []
        self.raidersIDs = []
        self.bannedIDs = []
        self.failedBanIDs = []

        self.antiraid_config_db = SimpleDB(self.bot.globaldata["dbdir"], "antiraid")

        self.safemode = True #only pretends to ban
        self.autopilot = True #automatic enabling of antiraid
        self.antiraid = False #banning any new user joining

        self.detected_raid_in_progress = False
        self.end_raid_timer_task = None
    
    @commands.Cog.listener()
    async def on_ready(self):
        if self.loaded:
            return
        self.loaded = True
        
        self.alert_channel = self.bot.get_channel(self.bot.config.alert_channel_id)

        data = await self.antiraid_config_db.getData()
        self.safemode = data["safemode"]
        self.autopilot = data["autopilot"]

    async def setVar(self, *, autopilot=None, safemode=None):
        """Helper function to keep variables synchronized with the database."""
        if autopilot is not None:
            self.autopilot = autopilot
        if safemode is not None:
            self.safemode = safemode
        data = {}
        data["autopilot"] = self.autopilot
        data["safemode"] = self.safemode
        await self.antiraid_config_db.saveData(data)


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return
        
        self.all_joins.append(member)

        #remember the new join
        self.joins.append((datetime.now(), member))
        #forget the oldest join
        #(basically "if", but using "while" to recover from unexpected cases)
        while len(self.joins) > join_queue_length:
            self.joins.popleft()
        

        #prolong end_raid timer
        if self.detected_raid_in_progress:
            if self.end_raid_timer_task:
                self.end_raid_timer_task.cancel()
            self.end_raid_timer_task = asyncio.create_task(self.countdown())
        
        #handle joined member during a raid 
        if self.antiraid:
            await self.banRaider(member.id)
        elif self.detected_raid_in_progress:
            self.raidersIDs.append(member.id)
        

        #check if the joins in the queue look like a raid
        if not self.detected_raid_in_progress and len(self.joins) == join_queue_length:
            allJoinsAreTooQuick = True #temporary
            previous = None
            first = True
            for (timestamp, member) in self.joins:
                if not first and (timestamp - previous[0]).total_seconds() > time_spacing:
                    allJoinsAreTooQuick = False
                    break
                previous = (timestamp, member)
                first = False
            
            #raid detected
            if allJoinsAreTooQuick:
                retroactive = list(self.joins)
                await self.raidStartDetected()
                for (_, raider) in retroactive:
                    await self.banRaider(raider.id)
    

    async def countdown(self):
        await asyncio.sleep(raid_end_countdown)
        await self.raidEndDetected()


    async def raidStartDetected(self):
        msgText = "------------------------------------------\n⚠️ __**RAID DETECTED!!!**__ ⚠️\n"
        if self.antiraid:
            msgText += f"✅ ..but you **already have antiraid mode enabled**, so everyone joining is already getting {'~~banned~~ (except not really, since safe mode is enabled)' if self.safemode else 'banned'}.\n"
            if self.autopilot:
                msgText += "*The antiraid will be automatically disabled when the raid ends. No further action is necessary.*\n"
            else:
                msgText += "*Antiraid is currently being controlled manually, so remember to disable it when the raid ends!*\n"
        elif self.autopilot:
            msgText += f"✅ **Antiraid has been automatically enabled!** {'~~' if self.safemode else ''}Raiders are getting banned...{'~~ (except not really, since safe mode is enabled)' if self.safemode else ''}\n"
            msgText += "*The antiraid will be automatically disabled when the raid ends. No further action is necessary.*\n"
        else:
            msgText += "❌ **No action is being taken!**\n"
            msgText += "*If you wish to take action, you can enable antiraid manually, or turn on the autopilot.*\n"
        msgText += "------------------------------------------"
        
        self.detected_raid_in_progress = True
        if self.autopilot:
            self.antiraid = True
        self.end_raid_timer_task = asyncio.create_task(self.countdown())

        await self.alert_channel.send(msgText)
    

    async def raidEndDetected(self):
        msgText = "------------------------------------------\n🎉 __**RAID ENDED!**__ 🎉\n"
        if self.autopilot:
            msgText += "✅ **Antiraid has been automatically disabled!** Nobody new is getting banned now.\n"
            msgText += "*No further action is necessary.*\n"
        else:
            if self.antiraid:
                msgText += f"❌ No action is being taken, **antiraid is still enabled** and the {'~~' if self.safemode else ''}**banning continues!**{'~~ (except not really, since safe mode is enabled)' if self.safemode else ''}\n"
                msgText += "Antiraid is currently being controlled manually, so you need to go disable it yourself.\n"
            else:
                msgText += "✅ ..and **you already disabled antiraid**, so nobody new is getting banned.\n"
                msgText += "*No further action is necessary now, unless another raid starts.*\n"
        msgText += "------------------------------------------"
        
        self.detected_raid_in_progress = False
        if self.autopilot:
            self.antiraid = False

        msg = await self.alert_channel.send(msgText)

        await self.sendResults(msg, not self.antiraid)


    async def banRaider(self, raiderID: int) -> bool:
        self.raidersIDs.append(raiderID)

        success = True
        try:
            user = await self.bot.fetch_user(raiderID)
        except:
            user = False
        
        if user:
            try:
                if self.safemode:
                    print(f"Antiraid: User <@{raiderID}> has been sent ban message: {raidBanMessage}")
                else:
                    await user.send(raidBanMessage)
                await asyncio.sleep(1)
            except:
                await self.alert_channel.send(f"Antiraid: failed to DM <@{raiderID}> while banning.")
            
            try:
                if self.safemode:
                    print(f"Antiraid: User <@{raiderID}> would be banned.")
                else:
                    await self.bot.main_guild.ban(user, reason="raid", delete_message_days=0)
                self.bannedIDs.append(raiderID)
            except:
                self.failedBanIDs.append(raiderID)
                await self.alert_channel.send(f"Antiraid: failed to ban <@{raiderID}>")
                success = False
        else:
            self.failedBanIDs.append(raiderID)
            await self.alert_channel.send(f"Antiraid: failed to ban <@{raiderID}>, user not found!")
            success = False

        return success


    async def sendResults(self, replyMsg: discord.Message, resetData: bool = False):
        if len(self.bannedIDs) > 0 or len(self.failedBanIDs) > 0:
            await replyMsg.reply(
                files=[
                    textFileAttachment("detected_raiders.txt", "\n".join([str(id) for id in self.raidersIDs])),
                    textFileAttachment("banned_users.txt", "\n".join([str(id) for id in self.bannedIDs])),
                    textFileAttachment("failed_to_ban.txt", "\n".join([str(id) for id in self.failedBanIDs]))
                ],
                mention_author=False
            )
        else:
            await replyMsg.reply(
                file=textFileAttachment("detected_raiders.txt", "\n".join([str(id) for id in self.raidersIDs])),
                mention_author=False
            )
        
        if resetData:
            self.raidersIDs = []
            self.bannedIDs = []
            self.failedBanIDs = []


    @commands.command(name="antiraid")
    async def antiraidCmd(self, ctx: commands.Context, state: str = ""):
        """Enables / disables the antiraid. The bot will ban any newly joining users until it's disabled."""
        
        if not self.bot.permhelper.isUserAbove(ctx.author, 150):
            await ctx.reply("You do not have permission to run this command! (Required level = 150)", mention_author=False)
            return
        
        if state=="":
            await ctx.reply(f"Antiraid is currently **{'enabled' if self.antiraid else 'disabled'}**.", mention_author=False)
            return
        
        if state=="enable":
            if self.antiraid:
                await ctx.reply("**Antiraid is already enabled!**", mention_author=False)
            else:
                self.antiraid = True
                await self.alert_channel.send("------------------------------------------\nAntiraid has been manually enabled!\n------------------------------------------")
                await ctx.reply("**Antiraid has been enabled!**\nAny user who joins will be automatically banned.", mention_author=False)
            return
        
        if state=="disable":
            if not self.antiraid:
                await ctx.reply("**Antiraid is already disabled!**", mention_author=False)
            else:
                self.antiraid = False
                msg = await self.alert_channel.send("------------------------------------------\nAntiraid has been manually disabled!\n------------------------------------------")
                await self.sendResults(msg, True)
                await ctx.reply("**Antiraid has been disabled!**\nNewly joined users will no longer get banned.", mention_author=False)
            return
        
        raise commands.BadArgument("Invalid argument")

    @antiraidCmd.error
    async def antiraidCmdError(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.BadArgument) or isinstance(error, commands.ConversionError):
            await ctx.reply(f"Command failed - invalid syntax.\nUse `{self.bot.config.bot_prefix}antiraid [enable/disable]`.", mention_author=False)
        else:
            await ctx.reply(f"Command failed.\n`{error.__class__.__name__}: {error}`", mention_author=False)

    

    @commands.command(name="antiraidAutopilot")
    async def antiraidAutopilotCmd(self, ctx: commands.Context, state: str = ""):
        """Enables / disables the automatic handling of raids. Banning will start and stop automatically."""
        
        if not self.bot.permhelper.isUserAbove(ctx.author, 100):
            await ctx.reply("You do not have permission to run this command! (Required level = 100)", mention_author=False)
            return
        
        if state=="":
            await ctx.reply(f"Antiraid autopilot is currently **{'enabled' if self.autopilot else 'disabled'}**.", mention_author=False)
            return
        
        if state=="enable":
            if self.autopilot:
                await ctx.reply("**Antiraid autopilot is already enabled!**", mention_author=False)
            else:
                await self.setVar(autopilot=True)
                msgText = "**Antiraid autopilot has been enabled!**\n"
                if self.detected_raid_in_progress:
                    if self.antiraid:
                        msgText += "The active antiraid (banning) will be automatically disabled when the raid stops."
                    else:
                        self.antiraid = True
                        await self.alert_channel.send("------------------------------------------\nAntiraid has been automatically enabled!\n------------------------------------------")
                        msgText += "Antiraid (banning) has been automatically enabled as well, since a raid is currently happening!"
                else:
                    if self.antiraid:
                        self.antiraid = False
                        await self.alert_channel.send("------------------------------------------\nAntiraid has been automatically disabled!\n------------------------------------------")
                        msgText += "Antiraid (banning) has been automatically disabled, since no raid is currently happening."
                    else:
                        msgText += "Antiraid (banning) will be automatically enabled when a raid starts."
                await ctx.reply(msgText, mention_author=False)
            return
        
        if state=="disable":
            if not self.autopilot:
                await ctx.reply("**Antiraid autopilot is already disabled!**", mention_author=False)
            else:
                await self.setVar(autopilot=False)
                msgText = "**Antiraid autopilot has been disabled!**\n"
                if self.detected_raid_in_progress:
                    msgText += "No action will be taken when the current raid stops."
                else:
                    msgText += "No action will be taken when a raid is detected."
                await ctx.reply(msgText, mention_author=False)
            return
        
        raise commands.BadArgument("Invalid argument")
    
    @antiraidAutopilotCmd.error
    async def antiraidAntipilotCmdError(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.BadArgument) or isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.ConversionError):
            await ctx.reply(f"Command failed - invalid syntax.\nUse `{self.bot.config.bot_prefix}antiraidAutopilot [enable/disable]`.", mention_author=False)
        else:
            await ctx.reply(f"Command failed.\n`{error.__class__.__name__}: {error}`", mention_author=False)


    @commands.command(name="antiraidSafemode")
    async def antiraidSafemodeCmd(self, ctx: commands.Context, state: str = ""):
        """Enables / disables the safe mode. During safe mode, the bot only pretends to ban."""
        
        if not self.bot.permhelper.isUserAbove(ctx.author, 100):
            await ctx.reply("You do not have permission to run this command! (Required level = 100)", mention_author=False)
            return
        
        if state=="":
            await ctx.reply(f"Antiraid safemode is currently **{'enabled' if self.autopilot else 'disabled'}**.", mention_author=False)
            return
        
        if state=="enable":
            if self.safemode:
                await ctx.reply(f"**Antiraid safemode is already enabled!**", mention_author=False)
            else:
                await self.setVar(safemode=True)
                await ctx.reply(f"**Antiraid safemode has been enabled!**\nThe bot will only pretend to ban.", mention_author=False)
            return
        
        if state=="disable":
            if not self.safemode:
                await ctx.reply(f"**Antiraid safemode is already disabled!**", mention_author=False)
            else:
                await self.setVar(safemode=False)
                await ctx.reply(f"**Antiraid safemode has been disabled!**\nBans will actually go through.", mention_author=False)
            return
        
        raise commands.BadArgument("Invalid argument")
    
    @antiraidSafemodeCmd.error
    async def antiraidSafemodeCmdError(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.BadArgument) or isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.ConversionError):
            await ctx.reply(f"Command failed - invalid syntax.\nUse `{self.bot.config.bot_prefix}antiraidSafemode [enable/disable]`.", mention_author=False)
        else:
            await ctx.reply(f"Command failed.\n`{error.__class__.__name__}: {error}`", mention_author=False)
    

    @commands.command(name="banJoinRange")
    async def banJoinRange(self, ctx: commands.Context, oldestUser: discord.User, newestUser: discord.User):
        """Bans all recently joined users in the given range."""
        
        if not self.bot.permhelper.isUserAbove(ctx.author, 150):
            await ctx.reply("You do not have permission to run this command! (Required level = 150)", mention_author=False)
            return
        
        firstID = oldestUser.id
        lastID = newestUser.id

        if firstID not in self.all_joins or lastID not in self.all_joins:
            await ctx.reply("Command failed - the specified range was not found in the join list.", mention_author=False)
            return
        
        await ctx.reply("Banning...", mention_author=False)

        self.raidersIDs = []
        self.bannedIDs = []
        self.failedBanIDs = []

        inRange = False
        for userID in reversed(self.all_joins):
            if not inRange and userID==firstID:
                inRange = True

            if inRange:
                await self.banRaider(userID)
            
            if inRange and userID==lastID:
                break
        
        msg = await ctx.reply(f"**Banning finished!** {len(self.bannedIDs)}/{len(self.raidersIDs)} users banned.", mention_author=True)
        await sendResults(msg, True)

    @banJoinRange.error
    async def banJoinRangeError(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.BadArgument) or isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.ConversionError):
            await ctx.reply(f"Command failed - invalid syntax.\nUse `{self.bot.config.bot_prefix}banJoinRange <firstUser> <lastUser>`.", mention_author=False)
        else:
            await ctx.reply(f"Command failed.\n`{error.__class__.__name__}: {error}`", mention_author=False)


def setup(bot: commands.Bot):
    bot.add_cog(Antiraid(bot))