import copy
from Core.BaseVars import baseVars
from Libs.Utils import sanitise_input
from fastapi.responses import JSONResponse


class Tags:
    def __init__(self, BaseVars: baseVars):
        self.BaseVars = BaseVars
        self.db = BaseVars.db["BlazesMod"]
        self.tags = self.db["Tags"]

    async def addTag(self, data: dict, websocket: bool = False):
        userid = sanitise_input(data["userid"])
        tag = sanitise_input(data["text"])
        x = await self.tags.find_one({"userid": userid})
        match x:
            case None:
                await self.tags.insert_one({"userid": userid, "tags": [tag]})
            case _:
                temp_tags = list(x["tags"])
                temp_tags.append(tag)
                await self.tags.update_one(
                    x, {"$set": {"userid": userid, "tags": temp_tags}}
                )

        match websocket:
            case False:
                return JSONResponse(
                    content={"response": f"UserID {userid} was tagged"}, status_code=200
                )
            case _:
                await websocket["Manager"].send_payload(
                    {
                        "payload": {
                            "type": "TagAdded",
                            "data": {"response": f"UserID {userid} was tagged"},
                        }
                    },
                    websocket["Socket"],
                )
                return

    async def removeTag(self, data: dict, websocket: bool = False):
        userid = sanitise_input(data["userid"])
        tag_id = int(data["tag_id"]) - 1
        x = await self.tags.find_one({"userid": userid})
        match x:
            case None:
                match websocket:
                    case False:
                        return JSONResponse(
                            content={"response": "No user id with this tag"},
                            status_code=404,
                        )
                    case _:
                        await websocket["Manager"].send_payload(
                            {
                                "payload": {
                                    "type": "TagRemoved",
                                    "data": {"response": "No user id with this tag"},
                                }
                            },
                            websocket["Socket"],
                        )
                        return
            case _:
                temp_tags = copy.deepcopy(list(x["tags"]))
                if tag_id in range(0, len(temp_tags)):
                    del temp_tags[tag_id]
                    await self.tags.update_one(
                        x, {"$set": {"userid": userid, "tags": temp_tags}}
                    )
                else:
                    match websocket:
                        case False:
                            return JSONResponse(
                                content={"response": "Tag ID is invalid"},
                                status_code=404,
                            )
                        case _:
                            await websocket["Manager"].send_payload(
                                {
                                    "payload": {
                                        "type": "TagRemoved",
                                        "data": {"response": "Tag ID is invalid"},
                                    }
                                },
                                websocket["Socket"],
                            )
                            return
        match websocket:
            case False:
                return JSONResponse(
                    content={
                        "response": f"UserID {userid} tag {tag_id + 1} was removed"
                    },
                    status_code=200,
                )
            case _:
                await websocket["Manager"].send_payload(
                    {
                        "payload": {
                            "type": "TagRemoved",
                            "data": {
                                "response": f"UserID {userid} tag {tag_id + 1} was removed"
                            },
                        }
                    },
                    websocket["Socket"],
                )
                return

    async def updateTag(self, data: dict, websocket: bool = False):
        userid = sanitise_input(data["userid"])
        tag_id = int(data["tag_id"]) - 1
        tag = str(data["text"])
        x = await self.tags.find_one({"userid": userid})
        match x:
            case None:
                match websocket:
                    case False:
                        return JSONResponse(
                            content={"response": "No user id with this tag"},
                            status_code=404,
                        )
                    case _:
                        await websocket["Manager"].send_payload(
                            {
                                "payload": {
                                    "type": "TagUpdated",
                                    "data": {"response": "No user id with this tag"},
                                }
                            },
                            websocket["Socket"],
                        )
                        return
            case _:
                temp_tags = copy.deepcopy(list(x["tags"]))
                if tag_id in range(0, len(temp_tags)):
                    temp_tags[tag_id] = tag
                    await self.tags.update_one(
                        x, {"$set": {"userid": userid, "tags": temp_tags}}
                    )
                else:
                    match websocket:
                        case False:
                            return JSONResponse(
                                content={"response": "Tag ID is invalid"},
                                status_code=404,
                            )
                        case _:
                            await websocket["Manager"].send_payload(
                                {
                                    "payload": {
                                        "type": "TagRemoved",
                                        "data": {"response": "Tag ID is invalid"},
                                    }
                                },
                                websocket["Socket"],
                            )
                            return
        match websocket:
            case False:
                return JSONResponse(
                    content={
                        "response": f"UserID {userid} tag {tag_id + 1} was updated"
                    },
                    status_code=200,
                )
            case _:
                await websocket["Manager"].send_payload(
                    {
                        "payload": {
                            "type": "TagUpdated",
                            "data": {
                                "response": f"UserID {userid} tag {tag_id + 1} was updated"
                            },
                        }
                    },
                    websocket["Socket"],
                )
                return

    async def fetchTags(self, websocket: bool = False):
        tags = []
        async for x in self.tags.find({}):
            temp_x = copy.deepcopy(x)
            del temp_x["_id"]
            tags.append(temp_x)
        match websocket:
            case False:
                return JSONResponse(content={"tags": tags}, status_code=200)
            case _:
                await websocket["Manager"].send_payload(
                    {"payload": {"type": "FetchedTags", "data": {"tags": tags}}},
                    websocket["Socket"],
                )
                return

    async def fetchTag(self, data: dict, websocket: bool = False):
        userid = str(data)
        x = await self.tags.find_one({"userid": sanitise_input(userid)})
        match x:
            case None:
                match websocket:
                    case False:
                        return JSONResponse(
                            content={"response": "UserID has no tags"}, status_code=404
                        )
                    case _:
                        await websocket["Manager"].send_payload(
                            {
                                "payload": {
                                    "type": "UserTag",
                                    "data": {"response": "UserID has no tags"},
                                }
                            },
                            websocket["Socket"],
                        )
                        return
            case _:
                temp_x = copy.deepcopy(x)
                del temp_x["_id"]
                match websocket:
                    case False:
                        return JSONResponse(
                            content={"response": temp_x}, status_code=200
                        )
                    case _:
                        await websocket["Manager"].send_payload(
                            {"payload": {"type": "UserTag", "data": {"tags": temp_x}}},
                            websocket["Socket"],
                        )
                        return
