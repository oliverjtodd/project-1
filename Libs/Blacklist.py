from fastapi.responses import JSONResponse
from Core.BaseVars import baseVars
from Libs.Utils import sanitise_input


class Blacklist:
    def __init__(self, BaseVars: baseVars):
        self.BaseVars = BaseVars
        self.db = BaseVars.db["BlazesMod"]
        self.avatars = self.db["Avatars"]
        self.blacklisted_authors = self.db["BlacklistedAuthors"]
        self.avatar_blacklist = self.db["AvatarBlacklist"]

    async def game_avatar_remove(self, data: dict):
        query = {"_id": sanitise_input(data["_id"])}
        x = await self.avatar_blacklist.find_one(query)
        match x:
            case None:
                return JSONResponse(
                    content={"response": "Avatar not in global blacklist"},
                    status_code=200,
                )
            case _:
                avatar = {"_id": sanitise_input(data["_id"]), "type": "Unknown"}
                await self.avatar_blacklist.delete_one(avatar)
                return JSONResponse(
                    content={"response": "Avatar removed from the global blacklist"},
                    status_code=200,
                )

    async def game_avatar_add(self, data: dict):
        query = {"_id": sanitise_input(data["_id"])}
        x = await self.avatar_blacklist.find_one(query)
        match x:
            case None:
                return JSONResponse(
                    content={"response": "Avatar already in global blacklist"},
                    status_code=200,
                )
            case _:
                avatar = {"_id": sanitise_input(data["_id"]), "type": "Unknown"}
                await self.avatar_blacklist.insert_one(avatar)
                return JSONResponse(
                    content={"response": "Avatar added to global blacklist"},
                    status_code=200,
                )

    async def search_avatar_add(self, data: dict):
        query = {"_id": {"$regex": sanitise_input(data["_id"])}}
        x = await self.avatars.find_one(query)
        match x:
            case None:
                return JSONResponse(
                    content={"response": "No avatar found by this id"}, status_code=200
                )
            case _:
                avatar = {"$set": {"BlacklistedFromSearch": True}}
                await self.avatars.update_one(query, avatar)
                return JSONResponse(
                    content={
                        "response": "Avatar was blacklisted from search",
                        "avatar_name": x["AvatarName"],
                    },
                    status_code=200,
                )

    async def search_avatar_remove(self, data: dict):
        query = {"_id": {"$regex": sanitise_input(data["_id"])}}
        x = await self.avatars.find_one(query)
        match x:
            case None:
                return JSONResponse(
                    content={"response": "No avatar found by this id"}, status_code=200
                )
            case _:
                avatar = {"$set": {"BlacklistedFromSearch": False}}
                await self.avatars.update_one(query, avatar)
                return JSONResponse(
                    content={
                        "response": "Avatar was un-blacklisted from search",
                        "avatar_name": x["AvatarName"],
                    },
                    status_code=200,
                )

    async def search_author_add(self, data: dict):
        # user = await self.vrcapi.fetchUser(data['data']['author_id'])
        author = await self.blacklisted_authors.find_one(
            {"_id": sanitise_input(data["author_id"])}
        )
        match author:
            case None:
                self.blacklisted_authors.insert_one({"_id": data["author_id"]})
                await self.avatars.update_many(
                    {
                        "AuthorID": {"$regex": data["author_id"]},
                        "ReleaseStatus": "private",
                    },
                    {"$set": {"BlacklistedFromSearch": True}},
                )
                return JSONResponse(
                    content={
                        "response": "Authors avatars have been blacklisted from search"
                    },
                    status_code=200,
                )
            case _:
                return JSONResponse(
                    content={
                        "response": "Author is already blacklisted",
                        "author_id": author["_id"],
                    },
                    status_code=403,
                )

    async def search_author_remove(self, data: dict):
        author = await self.blacklisted_authors.find_one(
            {"_id": sanitise_input(data["author_id"])}
        )
        match author:
            case None:
                return JSONResponse(
                    content={
                        "response": "The given author id is not blacklisted",
                        "author_id": author["_id"],
                    },
                    status_code=403,
                )
            case _:
                self.blacklisted_authors.delete_one({"_id": data["author_id"]})
                await self.avatars.update_many(
                    {"AuthorID": {"$regex": data["author_id"]}},
                    {"$set": {"BlacklistedFromSearch": False}},
                )
                return JSONResponse(
                    content={
                        "response": "Authors avatars have been un-blacklisted from search",
                        "author_id": data["author_id"],
                    },
                    status_code=200,
                )
