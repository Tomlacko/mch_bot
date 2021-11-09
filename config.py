TOKEN = "PUT_YOUR_TOKEN_HERE"

bot_prefix = "mch!"
bot_status_type = 0 #unknown = -1, playing = 0, streaming = 1, listening = 2, watching = 3, custom = 4, competing = 5
bot_status_message = "with commands"

bot_owner_id = 263862604915539969 #Tomlacko, can use Application owners if set to None

bot_logs_channel_id = 729090739702595596 #bot-logs
muted_role_id = 721780279643209789

log_onload_event = True #posts a message to bot-logs on startup

database_dir = "database"
cogs_dir = "cogs"
cogs = {
    "test_commands": True,
    "util_commands": True,
    "embed_creator": True,
    "welcome_messages": False,
    "new_accounts_alerts": True,
    "bottom_message": True,
    "joke_commands": True,
    "debugging": False
}

use_jishaku = True
