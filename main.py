import discord
from discord.ext import commands

from os import path

import config

from utils.permissions import PermissionHelper



intents = discord.Intents.default()
# pylint: disable=assigning-non-slot
intents.members = True

activity = discord.Activity(type=config.bot_status_type, name=config.bot_status_message)

bot = commands.Bot(
    command_prefix=config.bot_prefix,
    owner_id=config.bot_owner_id,
    intents=intents,
    allowed_mentions=discord.AllowedMentions(
        users=True,
        everyone=False,
        roles=False,
        replied_user=True
    ),
    activity=activity
)

bot.config = config
bot.permhelper = PermissionHelper(bot.config.permission_levels)
bot.globaldata = {}
bot.globaldata["status"] = {
    "cogs_total":0,
    "cogs_loaded":0,
    "cogs_failed":0,
    "cogs_disabled":0,
    "coglist":{}
}
bot.globaldata["cwd"] = path.dirname(__file__)
bot.globaldata["dbdir"] = path.join(bot.globaldata["cwd"], bot.config.database_dir)


def load_cogs(dir: str):
    print("\nLoading cogs...")

    botdata = bot.globaldata["status"]

    botdata["cogs_total"] += 1
    if bot.config.use_jishaku:
        try:
            bot.load_extension("jishaku")
        except:
            botdata["cogs_failed"] += 1
            botdata["coglist"]["jishaku"] = "Failed"
            print("x jishaku failed to load!")
        else:
            botdata["cogs_loaded"] += 1
            botdata["coglist"]["jishaku"] = "Loaded"
            print("+ jishaku loaded succesfully!")
    else:
        botdata["cogs_disabled"] += 1
        botdata["coglist"]["jishaku"] = "Disabled"

    for ext_name, ext_enabled in config.cogs.items():
        botdata["cogs_total"] += 1
        if ext_enabled:
            success = False
            try:
                bot.load_extension(dir.replace("/", ".") + "." + ext_name)
            except Exception as e:
                botdata["cogs_failed"] += 1
                print(f"x Failed to load {ext_name}! Exception: {e}")
            else:
                botdata["cogs_loaded"] += 1
                success = True
                print(f"+ Loaded {ext_name} successfully.")
            
            if success:
                botdata["coglist"][ext_name] = "Loaded"
            else:
                botdata["coglist"][ext_name] = "Failed"
        else:
            botdata["cogs_disabled"] += 1
            botdata["coglist"][ext_name] = "Disabled"
            print(f"- Skipping {ext_name}...")
    
    print(f"Cog loading done, loaded {botdata['cogs_loaded']}/{botdata['cogs_total']} cogs. ({botdata['cogs_failed']} failed, {botdata['cogs_disabled']} skipped)\n")

    if botdata["cogs_failed"] > 0:
        if input("Some cogs failed to load. Load bot regardless? (y): ")!="y":
            print("Quitting...")
            exit()

load_cogs(bot.config.cogs_dir)


@bot.event
async def on_ready():
    #do not put code here?
    print("-----")
    print("Bot fully loaded!")

    if config.log_onload_event:
        logchannel = bot.get_channel(config.bot_logs_channel_id)
        await logchannel.send(f"**Bot loaded!**\n{bot.globaldata['status']['cogs_loaded']}/{bot.globaldata['status']['cogs_total']} cogs loaded, {bot.globaldata['status']['cogs_failed']} failed, {bot.globaldata['status']['cogs_disabled']} skipped.")
    


bot.run(bot.config.TOKEN)