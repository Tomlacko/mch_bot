import discord
from discord.ext import commands

import re
import dateutil.parser as dateparser
from jira import JIRA

from utils.commonutils import *


mojiraURL = "https://bugs.mojang.com"

panelcolors = {
    "Unresolved":0xC1C7D0,
    "Fixed":0x00FF00,
    "Won't Fix":0xFFFF00,
    "Duplicate":0xFF0000,
    "Incomplete":0xFF0000,
    "Works As Intended":0xFFFF00,
    "Cannot Reproduce":0xFF0000,
    "Invalid":0xFF0000,
    "Awaiting Response":0x0094FF,
    "Done":0x00FF00
}

issueLinkRegex = re.compile(r"bugs.mojang.com[a-zA-Z0-9/_\-]*/([a-zA-Z]+-\d+)")

def validateIssueKeyAndGetProjectKey(issueID: str) -> tuple:
    if not issueID or len(issueID)<3:
        return None
    
    i = issueID.rfind("-")
    if i<=0 or i>=len(issueID)-1:
        return None
    
    projectKey = issueID[0:i].upper() #up to but not including the dash
    issueIDnum = issueID[i+1:] #numeric id

    if not issueIDnum.isdigit():
        return None
    
    return projectKey #(projectKey, issueIDnum)


async def getIssueData(issueID: str) -> dict:
    try:
        issue = JIRA(mojiraURL).issue(issueID)
    except:
        return None
    x = issue.fields
    
    data = {}
    data["_issue"] = issue

    data["project_name"] = tryOrDefault(lambda: x.project.name, "(Unknown project)") #Minecraft: Java Edition
    data["project_id"] = tryOrDefault(lambda: x.project.key, "") #MC
    data["project_raw_id"] = tryOrDefault(lambda: x.project.id, None) #10400
    data["id"] = tryOrDefault(lambda: issue.key, issueID) #MC-236858
    data["title"] = tryOrDefault(lambda: x.summary, "(Unknown issue title)") #title of the issue
    data["description"] = tryOrDefault(lambda: x.description, "") #the whole description with html-like formatting
    data["type"] = tryOrDefault(lambda: x.issuetype, "(Unknown)") #always Bug
    data["status"] = tryOrDefault(lambda: x.status.name, "(Unknown)") #status: Resolved
    data["votes"] = tryOrDefault(lambda: x.votes.votes, 0)
    data["watchers"] = tryOrDefault(lambda: x.watches.watchCount, 0)
    data["attachment_count"] = tryOrDefault(lambda: len(x.attachment), 0)
    data["comments"] = tryOrDefault(lambda: x.comment.total, 0)
    data["reporter"] = tryOrDefault(lambda: x.reporter.displayName, "(Unknown)") #[role] username
    data["reporter_icon"] = tryOrDefault(lambda: getattr(x.reporter.avatarUrls, '48x48'), "https://bugs.mojang.com/secure/useravatar?size=small&avatarId=10123") #user avatar icon
    data["created_time"] = tryOrDefault(lambda: round(dateparser.parse(x.created).timestamp()), None) #unix timestamp
    data["assignee"] = tryOrDefault(lambda: x.assignee.displayName, "(Unassigned)") #[Mojang] username
    data["assignee_icon"] = tryOrDefault(lambda: getattr(x.assignee.avatarUrls, '48x48'), "https://bugs.mojang.com/secure/useravatar?size=small&avatarId=10123") #user avatar icon
    data["resolution"] = tryOrDefault(lambda: x.resolution.name, "Unresolved") #'Fixed'
    data["resolution_time"] = tryOrDefault(lambda: round(dateparser.parse(x.resolutiondate).timestamp()), None) #unix timestamp
    data["last_updated"] = tryOrDefault(lambda: round(dateparser.parse(x.updated).timestamp()), None) #unix timestamp
    data["category"] = tryOrDefault(lambda: ", ".join([c.value for c in x.customfield_11901]), "(None)") #Category: 0: Entities, 1:...
    data["labels"] = tryOrDefault(lambda: (", ".join(x.labels)) if x.lables else "(None)", "(None)") #labels

    data["linked_issues"] = tryOrDefault(lambda: len(x.issuelinks), 0) #total linked issues
    data["duplicate_issues"] = 0
    data["related_issues"] = 0
    data["clone_issues"] = 0
    if data["linked_issues"] > 0:
        for iss in x.issuelinks:
            if iss.type.name=="Duplicate":
                data["duplicate_issues"] += 1
            elif iss.type.name=="Relates":
                data["related_issues"] += 1
            elif iss.type.name=="Cloners":
                data["clone_issues"] += 1

    #pick a preview image from attachments
    data["image"] = None
    if data["attachment_count"] > 0:
        for att in x.attachment:
            if att.mimeType.startswith("image/"):
                data["image"] = att.content
                break

    return data


async def getIssueDataMC(issueID: str) -> dict:
    data = await getIssueData(issueID)
    if not data:
        return
    issue = data["_issue"]
    x = issue.fields
    
    data["confirmation"] = tryOrDefault(lambda: x.customfield_10500.value, "(Unknown)") #confirmation status: Confirmed
    data["priority"] = tryOrDefault(lambda: x.customfield_12200.value, "(Unspecified)") #mojang priority: Important

    data["fix_version"] = tryOrDefault(lambda: x.fixVersions[-1].name, "(None)") #last version to which a fix applies
    data["first_affected_version"] = tryOrDefault(lambda: x.versions[0].name, "(Unknown)") #first version that was affected
    data["last_affected_version"] = tryOrDefault(lambda: x.versions[-1].name, "(Unknown)") #last version that was affected

    return data






class MojiraEmbeds(commands.Cog):
    """Replies to every bugs.mojang.com link with an embed detailing the issue. Additionally triggerable by a command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """If an URL leading to an issue is found, it posts an embed with details about the issue."""
        if message.author.bot:
            return
        
        issues = re.findall(issueLinkRegex, message.content)
        
        if len(issues)==1:
            ctx = await self.bot.get_context(message)
            await self.showMojiraEmbed(ctx, issues[0], True)
    

    @commands.command(name="mojira")
    async def mojiraCommand(self, ctx: commands.Context, issueID: str):
        """Posts an embed with details about the issue."""
        await self.showMojiraEmbed(ctx, issueID, False)
    
    @mojiraCommand.error
    async def mojiraCommandError(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument) or isinstance(error, commands.ConversionError):
            await ctx.reply(f"Command failed - bad formatting.\nUse `{self.bot.config.bot_prefix}mojira <bug-id>` (Example of bug-id: `MC-1337`).", mention_author=False)
        else:
            await ctx.reply("Command failed.", mention_author=False)
    
    
    async def showMojiraEmbed(self, ctx: commands.Context, issueID: str, hideErrors: bool = True):
        """Posts an embed with details about the issue."""
        projectID = validateIssueKeyAndGetProjectKey(issueID)

        if not projectID:
            if not hideErrors:
                await ctx.reply("Command failed - invalid issue ID!", mention_author=False)
            return
        
        issueID = issueID.upper()

        if projectID=="MC":
            data = await getIssueDataMC(issueID)
            if not data:
                if not hideErrors:
                    await ctx.reply(f"Command failed:\nFailed to obtain issue data from <https://bugs.mojang.com/browse/{issueID}>", mention_author=False)
                return

            embed=discord.Embed(title=data["title"],
                url=f"https://bugs.mojang.com/browse/{data['id']}",
                #description=data["description"],
                color=panelcolors.get(data["resolution"], 0x000000)
            )
            
            embed.set_author(
                name=f"{data['id']} • {data['project_name']}",
                url=f"https://bugs.mojang.com/browse/{data['id']}",
                icon_url=f"https://bugs.mojang.com/secure/projectavatar?pid={data['project_raw_id']}"
            )
            
            if data.get("image"):
                embed.set_thumbnail(url=data["image"])
#column1:
            embed.add_field(name="Status:", value=f"""{data["status"]}
**Resolution:**
{data["resolution"]}

**Resolution date:**
{(f"<t:{data['resolution_time']}:d> <t:{data['resolution_time']}:t>{NEW_LINE}(<t:{data['resolution_time']}:R>)") if data["resolution_time"] else "(None)"}""", inline=True)

#column2:
            embed.add_field(name="Confirmation:", value=f"""{data["confirmation"]}

**Priority:**
{data["priority"]}

**Votes:**
{data["votes"]}""", inline=True)

#column3:
            embed.add_field(name="Assignee:", value=f"""{data["assignee"]}

**Reported by:**
{data["reporter"]}
**Report date:**
<t:{data["created_time"]}:d> <t:{data["created_time"]}:t>
(<t:{data["created_time"]}:R>)""", inline=True)

#column4: (begins with non-breaking space)
            embed.add_field(name="​\nFirst affected version:", value=f"""{data["first_affected_version"]}
**Last affected version:**
{data["last_affected_version"]}
**Fixed in version:**
{data["fix_version"]}""", inline=True)

#column5: (begins with non-breaking space)
            embed.add_field(name="​\nCategory:", value=f"""{data["category"]}

**Labels:**
{data["labels"]}""", inline=True)

#footer (begins with non-breaking space)
            footer = f"""​
{data["linked_issues"]} linked issue{pluralSuffix(data["linked_issues"])} (\
{data["duplicate_issues"]} duplicate{pluralSuffix(data["duplicate_issues"])}, \
{(f"{data['clone_issues']} clone{pluralSuffix(data['clone_issues'])}, ") if data["clone_issues"]>=1 else ""}\
{data["related_issues"]} related issue{pluralSuffix(data['related_issues'])})
{data["comments"]} comment{pluralSuffix(data['comments'])} • {data["watchers"]} watcher{pluralSuffix(data["watchers"])}"""
            embed.set_footer(text=footer)

            await ctx.reply(embed=embed, mention_author=False)
        elif projectID in ["BDS", "MCPE", "MCCE", "MCL", "REALMS", "WEB"]:
            if not hideErrors:
                await ctx.reply("Command failed - Issues from the specified project aren't supported yet, sorry!", mention_author=False)
        else:
            if not hideErrors:
                await ctx.reply("Command failed - Invalid project ID!", mention_author=False)





def setup(bot: commands.Bot):
    bot.add_cog(MojiraEmbeds(bot))