import motor.motor_asyncio
import json
import asyncio
from tqdm import tqdm
from colorama import init, Fore
import datetime
import pathlib
import os
import re
import webbrowser

class Logger:
    def __init__(self):
        """Logging module"""
        init()
    
    def writeLog(self, data):
        date = datetime.datetime.now().strftime('%Y-%m-%d')
        with open(pathlib.Path(f"Logs/Backup-{date}.log"), "a+") as x:
            x.write(f"{data}\n")
    
    def info(self, info):
        """Out put info message"""
        self.writeLog(f"INFO:        {info}")
        print(f"{Fore.BLUE}INFO{Fore.WHITE}:     {info}")
    
    def success(self, success):
        """Out put success message"""
        self.writeLog(f"SUCCESS:  {success}")
        print(f"{Fore.GREEN}SUCCESS{Fore.WHITE}:  {success}")

    def error(self, error):
        """Out put error message"""
        self.writeLog(f"ERROR:     {error}")
        print(f"{Fore.RED}ERROR{Fore.WHITE}:    {error}")

    def warning(self, warning):
        """Out put warning message"""
        self.writeLog(f"WARNING:  {warning}")
        print(f"{Fore.YELLOW}WARNING{Fore.WHITE}:  {warning}")

class AutoBackUp:
    def __init__(self):
        self.dbKey = None
        self.log = Logger()
        self.db = None
        self.collections = []

    def fetchConfig(self):
        self.dbKey = "mongodb://blazesmodadmin:QJJge6nVGQWyhERggsYg4eHXgBHFt4PTEACpusYQQtKehK3hUMfcpqc@134.209.162.174:37914/BlazesMod?authSource=BlazesMod"

    def dbcon(self):
        self.log.info("Connecting to database")
        try:
            db = motor.motor_asyncio.AsyncIOMotorClient(self.dbKey)
            self.db = db['BlazesMod']
            self.log.success("DB connected")
        except:
            self.log.error("Unable to connect to database")
            exit()

    async def getCollections(self):
        self.log.info("Listing collections")
        list_names = await self.db.list_collection_names()
        self.log.info("===== [ Current collections in database ] =====")
        for x in list_names:
            self.log.info(f"Document -> {x}")
            self.collections.append(x)
        self.log.info("===============================================")

    async def backup(self):
        self.fetchConfig()
        self.log.success("Fetched db key")
        self.dbcon()
        self.log.success("Got database object")
        await self.getCollections()
        for x in tqdm(self.collections):
            self.log.info(f"Exporting {x}")
            data = []
            async for i in self.db[x].find({}):
                if isinstance(i['_id'], str) is False:
                    del i['_id']
                data.append(i)
            self.log.success("Writing export to file")
            os.system(f"mkdir Backup/{datetime.datetime.now().strftime('%Y-%m-%d')}")
            with open(pathlib.Path(f"Backup/{datetime.datetime.now().strftime('%Y-%m-%d')}/{x}.json"), "w") as r:
                json.dump(data, r, indent = 3)
    async def test(self):
        self.fetchConfig()
        self.dbcon()
        self.log.success("Got database object")
        key_words = ["nanachi", "nsfw"]
        aggregate_list = []
        reg = ""
        for keyword in key_words:
            reg = reg + f"(?i)({keyword})(?s:.*?)"
        #reg = reg[:-8]
        print(reg)
        aggregate_list.append({"$match" : {
                "AvatarName" : {"$regex": reg}
            }})
        aggregate_list.append({
                "$sample": {
                    "size": 1
                }
            })
        async for x in self.db['Avatars'].aggregate(aggregate_list):
            print(json.dumps(x, indent=3))
            #webbrowser.open_new_tab(x['ImageURL'])
asyncio.run(AutoBackUp().test())