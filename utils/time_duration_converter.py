from discord.ext.commands import Converter, Context, BadArgument
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta

class TimeDuration(Converter):
    """Tries to convert a string representing a duration of time (yMwdhms) into a timedelta object, respecting the calendar."""

    async def convert(self, ctx: Context, argument: str) -> timedelta:
        try:
            return getTimeDuration(argument)
        except:
            raise BadArgument("Time duration format not recognized!")

class TimeDurationSeconds(Converter):
    """Tries to convert a string representing a duration of time (yMwdhms) into seconds, respecting the calendar."""

    async def convert(self, ctx: Context, argument: str) -> timedelta:
        try:
            return round(getTimeDuration(argument).total_seconds())
        except:
            raise BadArgument("Time duration format not recognized!")


def getTimeDuration(val: str) -> timedelta:
    
    duration = {
        "y":0, #years
        "M":0, #months
        "w":0, #weeks
        "d":0, #days
        "h":0, #hours
        "m":0, #minutes
        "s":0, #seconds
    }

    digits = ""
    success = False
    for ch in val:
        if ch in "0123456789":
            digits += ch
            success = False
        elif ch in "yMwdhms":#end of segment
            if not digits or duration[ch]!=0:#fail if multiple letters or duplicate segment type
                success = False
                break
            #remember segment
            duration[ch] = int(digits)
            digits = ""
            success = True
        else:#unrecognized character
            success = False
            break
    
    if not success:
        raise ValueError("Time duration format not recognized!")
    
    currentDatetime = datetime.now()
    futureDatetime = currentDatetime + relativedelta(years=duration["y"], months=duration["M"], weeks=duration["w"], days=duration["d"], hours=duration["h"], minutes=duration["m"], seconds=duration["s"])
    
    return futureDatetime-currentDatetime