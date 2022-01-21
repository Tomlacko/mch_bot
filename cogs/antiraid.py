import discord
from discord.ext import commands

import asyncio
from datetime import datetime
from collections import deque

from utils.commonutils import textFileAttachment, list_find
from utils.simpledb import SimpleDB



join_queue_length = 5 #the amount of users that have to join quickly after each other to triger the antiraid. (value must be 2 or more)
time_spacing = 5 #seconds #if the spacing between each join is lower than this, then it is considered a raid
raid_end_countdown_time = 20 #seconds #time that has to pass after the last join to assume that the raid has ended

raidBanMessage = "You have been banned on the Minecraft@Home Discord server for being part of a raid.\nIf this was an accident, appeal here: https://discord.gg/9DwrQpH"
RAID_BAN_REASON = "raid"


class Antiraid(commands.Cog):
    """Monitors user joins and bans when a raid is detected."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.loaded = False
        self.alert_channel = None #temporary until loaded

        self.joins = deque([], join_queue_length)
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
        
        self.all_joins.append(member.id)

        #remember the new join
        self.joins.append((datetime.now(), member))
        #oldest join is automatically discarded thanks to deque.maxlen
        

        #prolong end_raid timer
        if self.detected_raid_in_progress:
            if self.end_raid_timer_task:
                self.end_raid_timer_task.cancel()
            self.end_raid_timer_task = asyncio.create_task(self.raidEndCountdown())
        
        #handle joined member during a raid 
        if self.detected_raid_in_progress:
            self.raidersIDs.append(member.id)
        if self.antiraid:
            await self.banAndLogRaider(member.id)
        

        #check if the joins in the queue look like a raid
        if not self.detected_raid_in_progress and len(self.joins) == join_queue_length:
            allJoinsAreTooQuick = True #temporary initial value
            previous = None
            first = True
            for (timestamp, member) in self.joins:
                #if one of the joins has a large enough time difference, give up, since it's not a raid
                if not first and (timestamp - previous[0]).total_seconds() > time_spacing:
                    allJoinsAreTooQuick = False
                    break
                previous = (timestamp, member)
                first = False
            
            #raid detected
            if allJoinsAreTooQuick:
                #remember the current joins, since the queue is gonna change during async execution
                retroactive = list(self.joins)
                self.raidersIDs = [u[1].id for u in retroactive]

                was_antiraid = self.antiraid
                await self.raidStartDetected()

                #retroactively ban initial raiders if antiraid got enabled
                if not was_antiraid and self.antiraid:
                    for (_, raider) in retroactive:
                        await self.banAndLogRaider(raider.id)
    

    async def raidEndCountdown(self):
        await asyncio.sleep(raid_end_countdown_time)
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
        self.end_raid_timer_task = asyncio.create_task(self.raidEndCountdown())

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
        msgText += f"{len(self.raidersIDs)} raiders detected in total:"
        
        self.detected_raid_in_progress = False

        was_antiraid = self.antiraid
        if self.autopilot:
            self.antiraid = False

        msg = await self.alert_channel.send(
            msgText,
            file=textFileAttachment("detected_raiders.txt", "\n".join([str(id) for id in self.raidersIDs]))
        )
        self.raidersIDs = []

        if was_antiraid and not self.antiraid:
            await self.sendBanResults(msg)


    async def banAndLogRaider(self, raiderID: int, output_channel: discord.TextChannel = None) -> bool:
        success = await self.banRaider(raiderID, self.alert_channel if output_channel is None else output_channel)
        (self.bannedIDs if success else self.failedBanIDs).append(raiderID)
        return success

    async def banRaider(self, raiderID: int, output_channel: discord.TextChannel = None) -> bool:
        """DMs every user before they get banned."""

        if output_channel is None:
            output_channel = self.alert_channel

        success = False

        #get user from id
        try:
            raider = await self.bot.fetch_user(raiderID)
        except:
            raider = False
        
        if raider:
            #DMing
            try:
                if self.safemode:
                    print(f"Antiraid safemode: User <@{raiderID}> would've been sent a ban message: {raidBanMessage}")
                else:
                    await raider.send(raidBanMessage)
                await asyncio.sleep(1)
            except:
                await output_channel.send(f"Failed to DM <@{raiderID}> while banning.")
            
            #Banning
            try:
                if self.safemode:
                    print(f"Antiraid safemode: User <@{raiderID}> would be banned.")
                else:
                    await self.bot.main_guild.ban(raider, reason=RAID_BAN_REASON, delete_message_days=0)
                success = True
            except:
                await output_channel.send(f"Failed to ban <@{raiderID}>.")
        #user not found
        else:
            await output_channel.send(f"Failed to ban <@{raiderID}> - user not found!")

        return success


    async def sendBanResults(self, replyMsg: discord.Message):
        total = len(self.bannedIDs) + len(self.failedBanIDs)
        if total > 0:
            await replyMsg.reply(
                f"__Antiraid results:__\n{len(self.bannedIDs)}/{total} users successfully banned.",
                files=[
                    textFileAttachment("banned_users.txt", "\n".join([str(id) for id in self.bannedIDs])),
                    textFileAttachment("failed_to_ban.txt", "\n".join([str(id) for id in self.failedBanIDs]))
                ],
                mention_author=False
            )
        else:
            await replyMsg.reply(
                "__Antiraid results:__\nNo users were banned.",
                mention_author=False
            )
        
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
                await self.sendBanResults(msg)
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
                        msgText += "The currently active antiraid (banning) will be automatically disabled when the raid stops."
                    else:
                        self.antiraid = True
                        await self.alert_channel.send("------------------------------------------\nAntiraid has been automatically enabled!\n------------------------------------------")
                        msgText += "Antiraid (banning) has been automatically enabled as well, since a raid is currently happening!"
                else:
                    if self.antiraid:
                        self.antiraid = False
                        msg = await self.alert_channel.send("------------------------------------------\nAntiraid has been automatically disabled!\n------------------------------------------")
                        await self.sendBanResults(msg)
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
        
        if not self.bot.permhelper.isUserAbove(ctx.author, 100):
            await ctx.reply("You do not have permission to run this command! (Required level = 100)", mention_author=False)
            return
        
        firstID = oldestUser.id
        lastID = newestUser.id

        first_index = list_find(self.all_joins, firstID)
        
        if first_index == -1:
            await ctx.reply("Command failed - the specified range was not found in the join list (initial user not found).", mention_author=False)
            return

        list_to_ban = self.all_joins[first_index:] #intentionally keeping a copy, since the list could change due to async execution
        
        if list_find(list_to_ban, lastID) == -1:
            await ctx.reply("Command failed - the specified range was not found in the join list (last user not found anywhere after first user).", mention_author=False)
            return


        await ctx.reply("Banning...", mention_author=False)

        bannedIDs = []
        failedBanIDs = []

        #ban all in the range
        for userID in list_to_ban:
            (bannedIDs if await self.banRaider(userID, ctx.channel) else failedBanIDs).append(userID)

            if userID == lastID:
                break
        
        total = len(bannedIDs) + len(failedBanIDs)
        if total > 0:
            await ctx.reply(
                f"**Banning finished!**\n{len(bannedIDs)}/{total} users successfully banned.",
                files=[
                    textFileAttachment("banned_users.txt", "\n".join([str(id) for id in bannedIDs])),
                    textFileAttachment("failed_to_ban.txt", "\n".join([str(id) for id in failedBanIDs]))
                ],
                mention_author=True
            )

    @banJoinRange.error
    async def banJoinRangeError(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.BadArgument) or isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.ConversionError):
            await ctx.reply(f"Command failed - invalid syntax.\nUse `{self.bot.config.bot_prefix}banJoinRange <firstUser> <lastUser>`.", mention_author=False)
        else:
            await ctx.reply(f"Command failed.\n`{error.__class__.__name__}: {error}`", mention_author=False)


    @commands.command(name="joinlist")
    async def joinlistCmd(self, ctx: commands.Context, limit: int = 0):
        """Sends a list of all the recently joined user IDs in reverse-chronological order."""

        if not self.bot.permhelper.isUserAbove(ctx.author, 100):
            await ctx.reply("You do not have permission to run this command! (Required level = 100)", mention_author=False)
            return
        
        if limit<=0 or limit>=len(self.all_joins):
            limit = len(self.all_joins)
            msgText = f"Here's the full list of newly joined users I have in memory: ({limit} in total, oldest to newest)"
        else:
            msgText = f"Here's a list of the last {limit}/{len(self.all_joins)} newly joined users I have in memory: (oldest to newest)"
        
        await ctx.reply(msgText, file=textFileAttachment("new_joins.txt", "\n".join([str(id) for id in self.all_joins[len(self.all_joins)-limit:]])), mention_author=False)

    @joinlistCmd.error
    async def joinlistCmdError(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.BadArgument) or isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.ConversionError):
            await ctx.reply(f"Command failed - invalid syntax.\nUse `{self.bot.config.bot_prefix}joinlist [limit]`.", mention_author=False)
        else:
            await ctx.reply(f"Command failed.\n`{error.__class__.__name__}: {error}`", mention_author=False)


def setup(bot: commands.Bot):
    bot.add_cog(Antiraid(bot))