import asyncio
import aiohttp
from Libs.Logger import Logger
from Core.BaseVars import baseVars


class TaskAPI:
    def __init__(self, BaseVars: baseVars):
        self.BaseVars = BaseVars
        self.db = BaseVars.db["BlazesMod"]
        self.avatars = self.db["Avatars"]
        self.users = self.db["Users"]
        self.searchLog = self.db["AvatarSearchLog"]
        self.archive = self.db["ArchiveAvatars"]
        self.avatar_blacklist = self.db["AvatarBlacklist"]
        self.BaseVars.dynamic_lists["avistats"] = {
            "Authors": "Not Calculated",
            "Avatars": "Not Calculated",
            "BlacklistedAvatars": "Not Calculated",
            "SearchesMade": "Not Calculated",
            "PrivateAvatars": "Not Calculated",
            "PublicAvatars": "Not Calculated",
        }
        self.log = Logger()

    async def regularLists(self):
        while True:
            self.BaseVars.dynamic_lists["aviblacklist"] = []
            async for x in self.avatar_blacklist.find({}):
                self.BaseVars.dynamic_lists["aviblacklist"].append(x)

            self.log.success(
                "Queryed avatar blacklist stats, waiting 60 seconds until next query"
            )
            await asyncio.sleep(60)

    async def lateLists(self):
        while True:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://nulls.sbs/D4gYaDPjd9g5FMAmny.json",
                    headers={"User-Agent": "GimmePhotonBotsPlz/1.0"},
                ) as res:
                    match res.status:
                        case 200:
                            res = await res.json()
                        case _:
                            res = None
            self.BaseVars.dynamic_lists["nullphotonbots"] = res
            self.log.success(
                "Queryed photon bot stats, waiting 3600 seconds until next query"
            )
            await asyncio.sleep(3600)

    async def avatarStats(self):
        while True:
            self.BaseVars.dynamic_lists["avistats"] = {
                "Authors": "Calculating...",
                "Avatars": "Calculating...",
                "BlacklistedAvatars": "Calculating...",
                "SearchesMade": "Calculating...",
                "PrivateAvatars": "Calculating...",
                "PublicAvatars": "Calculating...",
            }
            authors = await self.avatars.distinct("AuthorID")
            blacklisted = 0
            async for x in self.avatars.aggregate(
                [{"$match": {"BlacklistedFromSearch": True}}]
            ):
                blacklisted += 1
            private = 0
            async for x in self.avatars.aggregate(
                [{"$match": {"ReleaseStatus": "private"}}]
            ):
                private += 1
            public = 0
            async for x in self.avatars.aggregate(
                [{"$match": {"ReleaseStatus": "public"}}]
            ):
                public += 1
            _avatars = await self.db.command("collstats", "Avatars")
            searchrequests = await self.db.command("collstats", "AvatarSearchLog")
            self.BaseVars.dynamic_lists["avistats"] = {
                "Authors": len(authors),
                "Avatars": int(_avatars["count"]),
                "BlacklistedAvatars": blacklisted,
                "SearchesMade": int(searchrequests["count"]),
                "PrivateAvatars": private,
                "PublicAvatars": public,
            }
            self.log.success(
                "Queryed avatar stats, waiting 1200 seconds until next query"
            )
            await asyncio.sleep(1200)
