from discord.ext.commands import Converter, Context, BadArgument



class Autocolor(Converter):
    """Try to convert any color representation into a int rgb color code"""

    async def convert(self, ctx: Context, argument: str) -> int:
        try:
            return getColor(argument)
        except:
            raise BadArgument("Color not recognized!")


def getColor(val: str) -> int:
    val = val.replace("#", "").replace("(", "").replace(")", "").replace(",", " ").replace("  ", " ")
    splitval = val.split(" ")

    result = 0
    done = False

    if len(splitval)==3:
        r = min(int(splitval[0]), 255)
        g = min(int(splitval[1]), 255)
        b = min(int(splitval[2]), 255)
        result = r*256*256 + g*256 + b
        done = True
    elif len(splitval)==1:
        if len(val)==9 and val.isdecimal():
            r = min(int(val[0:3]), 255)
            g = min(int(val[3:6]), 255)
            b = min(int(val[6:]), 255)
            result = r*256*256 + g*256 + b
            done = True
        elif len(val)==6:
            try:
                result = int(val, 16)
                done = True
            except:
                pass
        else:
            try:
                result = int(val)
                done = True
            except:
                pass
        
    if done:
        if result<0 or result>16777215:
            raise ValueError("Color out of RGB range!")
        else:
            return result
    
    raise ValueError("Color not recognized!")