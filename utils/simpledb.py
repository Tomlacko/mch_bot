import aiofiles
import json

from os import path


class SimpleDB:
    def __init__(self, abs_dbdir_path, name):
        self.filepath = path.join(abs_dbdir_path, name+".json")
    
    async def getData(self):
        try:
            async with aiofiles.open(self.filepath, mode="r") as f:
                contents = await f.read()
            return json.loads(contents)
        except FileNotFoundError:
            return {}
    
    async def saveData(self, data):
        async with aiofiles.open(self.filepath, mode="w") as f:
            await f.write(json.dumps(data))
            await f.flush()