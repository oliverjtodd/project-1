import bson
from Core.BaseVars import baseVars
from Libs.HttpResponseHandler import Handler


class Moderation:
    def __init__(self, BaseVars: baseVars):
        self.BaseVars = BaseVars
        self.db = BaseVars.db["BlazesMod"]
        self.users = self.db["Users"]
        self.responsehandler = Handler()

    async def banUser(self, data: dict, clients: list, BaseVars: baseVars):
        try:
            keytoban = {"_id": {"$regex": str(data["authkey"])}}
            user = str(data["authkey"])
        except:
            keytoban = {"DiscordID": bson.Int64(data["discordid"])}
            user = bson.Int64(data["discordid"])
        reasonforban = data["reason"]
        await self.users.update_one(
            keytoban,
            {"$set": {"IsBanned": True, "BanReason": reasonforban}},
        )
        for ws in clients:
            if ws.Authkey == str(data["authkey"]):
                await BaseVars.ConnectionManager.send_payload(
                    {
                        "payload": {
                            "type": "AccessDenied",
                            "data": "You have been banned from the blaze mod network",
                        }
                    },
                    ws,
                )
                await BaseVars.ConnectionManager.close_socket(ws, 1008)
        return self.responsehandler.Moderation.setban(user, reasonforban)

    async def unbanUser(self, data: dict):
        try:
            keytounban = {"_id": {"$regex": str(data["authkey"])}}
            user = str(data["authkey"])
        except:
            keytounban = {"DiscordID": bson.Int64(data["discordid"])}
            user = bson.Int64(["discordid"])
        await self.users.update_one(
            keytounban,
            {"$set": {"IsBanned": False, "BanReason": None}},
        )
        return self.responsehandler.Moderation.unsetban(user)
