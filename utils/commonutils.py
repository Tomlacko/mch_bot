import discord
from io import StringIO
import traceback


NEW_LINE = '\n' #used in f-strings, where backslashes don't work


def snowflakeToTime(snowflake: int) -> int:
    return snowflake//4194304000 + 1420070400

def tryOrDefault(func, defaultVal=None):
    try:
        return func()
    except:
        pass
    return defaultVal

def pluralSuffix(val: int) -> str:
    if val!=1:
        return "s"
    return ""

def list_find(li, elem):
    for i in range(len(li)):
        if li[i] == elem:
            return i
    return -1

def list_rfind(li, elem):
    for i in reversed(range(len(li))):
        if li[i] == elem:
            return i
    return -1

def textFileAttachment(filename="attachment.txt", textContent="") -> discord.File:
    return discord.File(StringIO(textContent), filename=filename)

def get_exception_traceback(ex: Exception) -> str:
    return "".join(traceback.format_exception(type(ex), ex, ex.__traceback__))