TOKEN = "PUT_YOUR_TOKEN_HERE"

bot_prefix = "mch!"
bot_status_type = 2 #unknown = -1, playing = 0, streaming = 1, listening to = 2, watching = 3, custom = 4, competing = 5
bot_status_message = f"{bot_prefix} prefix"

bot_owner_id = 263862604915539969 #Tomlacko | will query Application owners if set to None

muted_role_id = 721780279643209789


bot_logs_channel_id = 729090739702595596 #bot-logs
send_message_on_startup = False
send_message_on_quit = False #only works when quitting through the console, for which use_console needs to be enabled

use_jishaku = True
use_console = True

database_dir = "database"
cogs_dir = "cogs"
cogs = {
    "test_commands": True,
    "util_commands": True,
    "embed_creator": True,
    "welcome_messages": False,
    "new_accounts_alerts": True,
    "bottom_message": True,
    "muteme": True,
    "mojira_embeds": True,
    "fun_commands": True,
    "mathstuff": True,
    "modmail": True,
    "andrew_thing": True,

    "debugging": False
}

permission_levels = {
    720725702516932658: 200, #Administrator
    774373485015072801: 150, #Server Mod
    738045010519392317: 140, #Bot+
    720725754605994087: 100, #Chat Mod
    889242293310214194: 90, #Bot
    720778741701410866: 70, #PPA
    722845569403322369: 50, #PCA
    756990603945967639: 20, #Member
    766083300682498088: 10, #Project Contributor
}