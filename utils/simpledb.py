import aiofiles
import json

from os import path


class SimpleDB:
    def __init__(self, abs_dir_path, name):
        self.filepath = path.join(abs_dir_path, name+".json")
    
    async def getData(self):
        async with aiofiles.open(self.filepath, mode='r') as f:
            contents = await f.read()
        return json.loads(contents)
    
    async def saveData(self, data):
        async with aiofiles.open(self.filepath, mode='w') as f:
            await f.write(json.dumps(data))