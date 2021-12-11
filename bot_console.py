import discord
from discord.ext import commands



#helper class
class BotConsoleCommand():
    """Allows for easier parsing of custom console commands"""

    def __init__(self, inp: str):
        self.inp = inp
        self.length = len(inp)
        self.index = 0
    
    def skipWhitespace(self):
        while self.index < self.length and self.inp[self.index].isspace():
            self.index+=1

    def getNextPart(self) -> str:
        self.skipWhitespace()
        part = ""
        start = self.index
        while self.index < self.length and not self.inp[self.index].isspace():
            self.index+=1
        return self.inp[start:self.index]
    
    def getRest(self) -> str:
        self.skipWhitespace()
        return self.inp[self.index:]






class BotConsole(commands.Cog):
    """Allows the bot owner to type stuff into the console."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channel = None
    

    async def receive_input(self, inp: str):
        command = BotConsoleCommand(inp)
        commandName = command.getNextPart()

        if commandName == "help":
            await self.help()
        elif commandName == "quit":
            await self.quit()
        elif commandName == "reload":
            await self.reload_cog(command.getRest())
        elif commandName == "setchannel":
            await self.set_channel(command.getRest())
        elif commandName == "post":
            await self.post(command.getRest())
    

    async def help(self):
        print("\nAvailable console commands:")
        print("------")
        print("help = prints this message")
        print("quit = stops the bot")
        print("reload <cogname> = reloads a cog")
        print("setchannel <channel_id> = sets a given channel as active, useful for other commands")
        print("post <message> = sends a message in a given channel")
        print("------")
    

    async def quit(self):
        print("Quitting...")
        if self.bot.config.send_message_on_quit and self.bot.logs_channel:
            await self.bot.logs_channel.send("Stopping the bot...")
        await self.bot.close()

    async def reload_cog(self, cogname: str):
        try:
            self.bot.reload_extension(cogname)
        except commands.ExtensionNotLoaded as err:
            print("Failed to load extension - extension is not loaded")
        except commands.ExtensionNotFound as err:
            print("Failed to load extension - extension not found")
        except (commands.NoEntryPointError, commands.ExtensionFailed) as err:
            print(f"Failed to load extension - error while loading extension: {type(err)}\n{err}")
        except BaseException as err:
            print(f"Failed to load extension - unexpected error: {type(err)}\n{err}")
        else:
            print("Extension reloaded succesfully.")
    

    async def set_channel(self, channelID: str):
        try:
            channelID = int(channelID)
        except:
            print("Command failed - invalid channel ID")
            return
        
        channel = self.bot.get_channel(channelID)
        if channel is None:
            print("Command failed - channel not found")
            return
        
        print(f"Channel set successfully.")
        self.channel = channel


    async def post(self, message: str):
        if self.channel is None:
            print("Command failed - no channel is selected! Use 'setchannel <channelID>' first!")
            return
        
        msg = await self.channel.send(message)
        if msg:
            print(f"Message sent! {msg.jump_url}")
        else:
            print("Message failed to send!")





def setup(bot: commands.Bot):
    bot.add_cog(BotConsole(bot))