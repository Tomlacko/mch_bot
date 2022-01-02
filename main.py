import discord
from discord.ext import commands

from os import path
import asyncio
from sys import stdin
from datetime import datetime

from utils.permissions import PermissionHelper
import config


intents = discord.Intents.all()#.default()
# pylint: disable=assigning-non-slot
#intents.members = True

activity = discord.Activity(type=config.bot_status_type, name=config.bot_status_message)

bot = commands.Bot(
    command_prefix=config.bot_prefix,
    owner_id=config.bot_owner_id,
    intents=intents,
    allowed_mentions=discord.AllowedMentions(
        users=True,
        replied_user=True,
        everyone=False,
        roles=False
    ),
    activity=activity
)

bot.is_loaded = False
bot.logs_channel = None #loaded later

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
    print("Loading core cogs...")

    botdata = bot.globaldata["status"]

    #load core cogs
    core_cogs = {
        "jishaku": bot.config.use_jishaku,
        "bot_console": bot.config.use_console
    }
    for ext_name, ext_enabled in core_cogs.items():
        botdata["cogs_total"] += 1
        if ext_enabled:
            try:
                bot.load_extension(ext_name)
            except:
                botdata["cogs_failed"] += 1
                botdata["coglist"][ext_name] = "Failed"
                print(f"x '{ext_name}' failed to load!")
            else:
                botdata["cogs_loaded"] += 1
                botdata["coglist"][ext_name] = "Loaded"
                print(f"+ '{ext_name}' loaded succesfully!")
        else:
            botdata["cogs_disabled"] += 1
            botdata["coglist"][ext_name] = "Disabled"

    print("Loading additional cogs...")

    #load additional cogs
    for ext_name, ext_enabled in config.cogs.items():
        botdata["cogs_total"] += 1
        if ext_enabled:
            success = False
            try:
                bot.load_extension(dir.replace("/", ".") + "." + ext_name)
            except Exception as e:
                botdata["cogs_failed"] += 1
                print(f"x Failed to load '{ext_name}'! Exception: {e}")
            else:
                botdata["cogs_loaded"] += 1
                success = True
                print(f"+ Loaded '{ext_name}' successfully.")
            
            if success:
                botdata["coglist"][ext_name] = "Loaded"
            else:
                botdata["coglist"][ext_name] = "Failed"
        else:
            botdata["cogs_disabled"] += 1
            botdata["coglist"][ext_name] = "Disabled"
            print(f"- Skipping '{ext_name}'...")
    
    print(f"Cog initializing done, loaded {botdata['cogs_loaded']}/{botdata['cogs_total']} cogs. ({botdata['cogs_failed']} failed, {botdata['cogs_disabled']} skipped)")

    if botdata["cogs_failed"] > 0:
        if input("Some cogs failed to load. Load bot regardless? (y): ")!="y":
            print("Quitting...")
            exit()


print("\n--- Starting the bot ---")
load_cogs(bot.config.cogs_dir)
print("---------------")
print("Bot is loading... (waiting for an on_ready event)")


@bot.event
async def on_ready():
    if bot.is_loaded:
        print(f"[{datetime.now()}] ***Bot reconnected***\n")
        return
    
    bot.is_loaded = True

    if config.bot_logs_channel_id:
        bot.logs_channel = bot.get_channel(config.bot_logs_channel_id)

    if bot.config.send_message_on_startup and bot.logs_channel:
        await bot.logs_channel.send(f"**Bot loaded!**\n{bot.globaldata['status']['cogs_loaded']}/{bot.globaldata['status']['cogs_total']} cogs loaded, {bot.globaldata['status']['cogs_failed']} failed, {bot.globaldata['status']['cogs_disabled']} skipped.")
    
    if bot.config.use_console:
        print("\n--- Done, bot fully loaded! (Type 'quit' to stop it.) ---\n")
        loop = asyncio.get_event_loop()
        loop.add_reader(stdin, relay_console_input)
    else:
        print("\n--- Done, bot fully loaded! (Press CTRL+C to stop it.) ---\n")
    
def relay_console_input():
    input_line = stdin.readline().rstrip("\n")
    
    #handle the input via a cog
    botConsole = bot.get_cog("BotConsole")
    if botConsole is not None:
        asyncio.create_task(botConsole.receive_input(input_line))


bot.run(bot.config.TOKEN)