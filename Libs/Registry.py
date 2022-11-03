import uuid
import bson
import hashlib
import copy
from fastapi.responses import JSONResponse
from Core.BaseVars import baseVars
from Libs.Utils import sanitise_input
from Libs.DataModel import DataModel
from Libs.Webhooks import Webhook


class Registry:
    def __init__(self, BaseVars: baseVars):
        self.BaseVars = BaseVars
        self.db = BaseVars.db["BlazesMod"]
        self.users = self.db["Users"]
        self.search_log = self.db["AvatarSearchLog"]
        self.webhook = Webhook(BaseVars)

    async def resetHWID(self, data: dict):
        x = await self.users.find_one({"_id": sanitise_input(data["authkey"])})
        match x:
            case None:
                return JSONResponse(
                    content={"response": "No user with this key"}, status_code=404
                )
            case _:
                await self.users.update_one(x, {"$set": {"HWID": None}})
                return JSONResponse(
                    content={"response": "Users HWID reset successfully"},
                    status_code=200,
                )

    def keyGen(self, username: str, did: bson.Int64):
        _uuid = str(uuid.uuid4()).upper()
        key_hash = hashlib.md5(str(_uuid).encode())
        _hash = hashlib.md5(str(f"{username}_{did}").encode())
        key = f"BM_{_uuid}_{key_hash.hexdigest()}"
        return {"Key": key, "Hash": _hash}

    async def regenUser(self, authCheck: dict, data: dict):
        x = await self.users.find_one({"_id": sanitise_input(data["authkey"])})
        match x:
            case None:
                return JSONResponse(
                    content={"response": "User does not exist"}, status_code=404
                )
            case _:
                user = copy.deepcopy(x)
                username = data["discordName"]
                discordid = data["discordID"]
                gen_key = self.keyGen(username, discordid)
                accessType = user["AccessType"]
                data['accessType'] = accessType
                await self.search_log.update_many(
                    {"DiscordID": sanitise_input(user["DiscordID"])},
                    {"$set": {"DiscordID": sanitise_input(user["DiscordID"])}},
                )
                await self.users.insert_one(
                    DataModel.userModel(
                        self,
                        key=gen_key["Key"],
                        discord_name=username,
                        discord_id=discordid,
                        user_hash=gen_key["Hash"].hexdigest(),
                        access_type=accessType,
                    )
                )
                await self.users.delete_one({"_id": data["authkey"]})
                response_register = {
                    "response": "Successfully registered user",
                    "data": {
                        "AuthKey": gen_key["Key"],
                        "HWID": None,
                        "DiscordName": username,
                        "DiscordID": discordid,
                        "UserHash": gen_key["Hash"].hexdigest(),
                        "IsBanned": False,
                        "BanReason": None,
                        "AccessType": accessType,
                        "ExtensionAccess": [],
                    },
                }
                await self.webhook.key_action_payload(authCheck, data)
                return JSONResponse(content=response_register, status_code=200)

    async def register(self, authCheck: dict, data: dict):
        username = data["discordName"]
        discordid = data["discordID"]
        gen_key = self.keyGen(username, discordid)
        print(gen_key)
        accessType = data["accessType"]
        if accessType in ["Developer", "Staff", "User", "External_API"]:
            await self.users.insert_one(
                DataModel.userModel(
                    self,
                    key=gen_key["Key"],
                    discord_name=username,
                    discord_id=discordid,
                    user_hash=gen_key["Hash"].hexdigest(),
                    access_type=accessType,
                )
            )
            response_register = {
                "response": "Successfully registered user",
                "data": {
                    "AuthKey": gen_key["Key"],
                    "HWID": None,
                    "DiscordName": username,
                    "DiscordID": discordid,
                    "UserHash": gen_key["Hash"].hexdigest(),
                    "IsBanned": False,
                    "BanReason": None,
                    "AccessType": accessType,
                    "ExtensionAccess": [],
                },
            }
            await self.webhook.key_action_payload(authCheck, data)
            return JSONResponse(content=response_register, status_code=200)
        else:
            return JSONResponse(
                content={
                    "response": "Invalid access role not in [Developer, Staff, User, External_API]"
                },
                status_code=403,
            )
