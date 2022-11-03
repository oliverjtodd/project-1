import aiohttp
import json
import asyncio
from fastapi import Request
from Libs.Schema import WebsocketBody
from Libs.Converters.Time import TimeConverter
from Core.BaseVars import baseVars


class Webhook:
    def __init__(self, BaseVars: baseVars):
        self.BaseVars = BaseVars
        self.log = BaseVars.log
        self.loop: asyncio.AbstractEventLoop = BaseVars.dynamic_lists["eventloop"]

    async def request(self, sender, payload: dict):
        async with aiohttp.ClientSession() as session:
            async with session.post(sender, json=payload) as x:
                code = x.status
                x = await x.read()
                self.log.info(
                    f"Response from discord: {x.decode('utf-8')} | Status code: {code}"
                )

    async def request_payload(self, data: Request):
        sender = self.BaseVars.API_REQUEST_WEBHOOK_URL
        payload = {
            "content": None,
            "embeds": [
                {
                    "title": "Headers",
                    "description": f"```json\n{json.dumps(dict(data.headers), indent = 3)}```",
                    "color": 65280,
                    "footer": {
                        "text": f"Logged at - {str(await TimeConverter.humanDate(self))}"
                    },
                }
            ],
        }
        await self.loop.create_task(self.request(sender, payload))

    async def authpass_payload(self, authCheck: dict, data: dict):
        sender = self.BaseVars.USER_WEBHOOK_URL
        locked = (
            f'\nLocked to HWID: `{data["HWID"]}`\n=================='
            if authCheck["HWID"] != data["HWID"]
            else ""
        )
        payload = {
            "content": None,
            "embeds": [
                {
                    "title": "Auth Passed",
                    "description": f"===== [User Info] =====\nDiscord Name: `{authCheck['DiscordName']}`\nDiscord ID: `{authCheck['DiscordID']}`\nMod Key: `{authCheck['AuthKey']}`\nHWID: `{authCheck['HWID']}`\n=================={locked}",
                    "color": 65280,
                    "footer": {
                        "text": f"Logged at - {str(await TimeConverter.humanDate(self))}"
                    },
                },
                {
                    "title": "Headers",
                    "description": f"```json\n{json.dumps(authCheck['Headers'], indent = 3)}```",
                    "color": 65280,
                    "footer": {
                        "text": f"Logged at - {str(await TimeConverter.humanDate(self))}"
                    },
                },
            ],
        }
        await self.loop.create_task(self.request(sender, payload))

    async def key_action_payload(self, authCheck: dict, data: dict):
        sender = self.BaseVars.REGISTRY_LOGS_WEBHOOK_URL
        payload = {
            "content": None,
            "embeds": [
                {
                    "title": f"Key Action",
                    "description": f"===== [User Info] =====\nDiscord Name: `{authCheck['DiscordName']}`\nDiscord ID: `{authCheck['DiscordID']}`\nMod Key: `{authCheck['AuthKey']}`\nHWID: `{authCheck['HWID']}`\n==================",
                    "color": 65280,
                    "fields": [
                        {
                            "name": "Discord ID",
                            "value": f"`({data['discordID']})`",
                        },
                        {
                            "name": "Discord Name",
                            "value": f"`({data['discordName']})`",
                        },
                        {
                            "name": "Access Type",
                            "value": f"`({data['accessType']})`",
                        },
                    ],
                    "footer": {
                        "text": f"Logged at - {str(await TimeConverter.humanDate(self))}"
                    },
                },
                {
                    "title": "Headers",
                    "description": f"```json\n{json.dumps(authCheck['Headers'], indent = 3)}```",
                    "color": 65280,
                    "footer": {
                        "text": f"Logged at - {str(await TimeConverter.humanDate(self))}"
                    },
                },
            ],
        }
        await self.loop.create_task(self.request(sender, payload))

    async def ban_payload(self, authCheck: dict):
        sender = self.BaseVars.USER_WEBHOOK_URL
        payload = {
            "content": None,
            "embeds": [
                {
                    "title": "Auth Fail: Key is banned",
                    "description": f"===== [User Info] =====\nDiscord Name: `{authCheck['DiscordName']}`\nDiscord ID: `{authCheck['DiscordID']}`\nMod Key: `{authCheck['AuthKey']}`\nHWID: `{authCheck['HWID']}`\n==================",
                    "color": 16716032,
                    "fields": [
                        {
                            "name": "Ban Reason",
                            "value": f"`({authCheck['BanReason']})`",
                        },
                    ],
                    "footer": {
                        "text": f"Logged at - {str(await TimeConverter.humanDate(self))}"
                    },
                },
                {
                    "title": "Headers",
                    "description": f"```json\n{json.dumps(authCheck['Headers'], indent = 3)}```",
                    "color": 16716032,
                    "footer": {
                        "text": f"Logged at - {str(await TimeConverter.humanDate(self))}"
                    },
                },
            ],
        }
        await self.loop.create_task(self.request(sender, payload))

    async def bluescreen_payload(self, authCheck: dict):
        sender = self.BaseVars.USER_WEBHOOK_URL
        payload = {
            "content": None,
            "embeds": [
                {
                    "title": "Auth Fail: Sending Bluescreen",
                    "description": f"===== [User Info] =====\nDiscord Name: `{authCheck['DiscordName']}`\nDiscord ID: `{authCheck['DiscordID']}`\nMod Key: `{authCheck['AuthKey']}`\nHWID: `{authCheck['HWID']}`\n==================",
                    "color": 16716032,
                    "footer": {
                        "text": f"Logged at - {str(await TimeConverter.humanDate(self))}"
                    },
                },
                {
                    "title": "Headers",
                    "description": f"```json\n{json.dumps(authCheck['Headers'], indent = 3)}```",
                    "color": 16716032,
                    "footer": {
                        "text": f"Logged at - {str(await TimeConverter.humanDate(self))}"
                    },
                },
            ],
        }
        await self.loop.create_task(self.request(sender, payload))

    async def key_payload(self, authCheck: dict):
        sender = self.BaseVars.USER_WEBHOOK_URL
        payload = {
            "content": None,
            "embeds": [
                {
                    "title": "Auth Fail: Invalid key",
                    "description": f"===== [User Info] =====\nDiscord Name: `{authCheck['DiscordName']}`\nDiscord ID: `{authCheck['DiscordID']}`\nMod Key: `{authCheck['AuthKey']}`\nHWID: `{authCheck['HWID']}`\n==================",
                    "color": 16716032,
                    "footer": {
                        "text": f"Logged at - {str(await TimeConverter.humanDate(self))}"
                    },
                },
                {
                    "title": "Headers",
                    "description": f"```json\n{json.dumps(authCheck['Headers'], indent = 3)}```",
                    "color": 16716032,
                    "footer": {
                        "text": f"Logged at - {str(await TimeConverter.humanDate(self))}"
                    },
                },
            ],
        }
        await self.loop.create_task(self.request(sender, payload))

    async def hwid_payload(self, authCheck: dict, data: dict):
        sender = self.BaseVars.USER_WEBHOOK_URL
        payload = {
            "content": None,
            "embeds": [
                {
                    "title": "Auth Fail: Invalid HWID",
                    "description": f"===== [User Info] =====\nDiscord Name: `{authCheck['DiscordName']}`\nDiscord ID: `{authCheck['DiscordID']}`\nMod Key: `{authCheck['AuthKey']}`\nHWID: `{authCheck['HWID']}`\n==================\n",
                    "color": 16716032,
                    "fields": [
                        {
                            "name": "HWID Is Incorrect",
                            "value": f"`({data['HWID']})` does not match `({authCheck['HWID']})`",
                        },
                    ],
                    "footer": {
                        "text": f"Logged at - {str(await TimeConverter.humanDate(self))}"
                    },
                },
                {
                    "title": "Headers",
                    "description": f"```json\n{json.dumps(authCheck['Headers'], indent = 3)}```",
                    "color": 16716032,
                    "footer": {
                        "text": f"Logged at - {str(await TimeConverter.humanDate(self))}"
                    },
                },
            ],
        }
        await self.loop.create_task(self.request(sender, payload))

    async def avatarsearch_payload(
        self, authCheck: dict, data: dict, searchtype: str, results: int
    ):
        sender = self.BaseVars.SEARCH_AVATAR_WEBHOOK_URL
        payload = {
            "content": None,
            "embeds": [
                {
                    "title": "Avatar Searched",
                    "description": f"===== [User Info] =====\nDiscord Name: `{authCheck['DiscordName']}`\nDiscord ID: `{authCheck['DiscordID']}`\nMod Key: `{authCheck['AuthKey']}`\nHWID: `{authCheck['HWID']}`\n==================",
                    "color": 16761856,
                    "fields": [
                        {"name": "Search Type:", "value": f"`{searchtype}`"},
                        {"name": "Query:", "value": f"`{data}`"},
                        {"name": "Results:", "value": f"`{results}`"},
                    ],
                    "footer": {
                        "text": f"Logged at - {str(await TimeConverter.humanDate(self))}"
                    },
                }
            ],
        }
        await self.loop.create_task(self.request(sender, payload))

    async def websocket_avatarsearch_payload(
        self, websocket: WebsocketBody, data: dict, searchtype, results
    ):
        sender = self.BaseVars.SEARCH_AVATAR_WEBHOOK_URL
        payload = {
            "content": None,
            "embeds": [
                {
                    "title": "Avatar Searched",
                    "description": f"===== [User Info] =====\nDiscord Name: `{websocket.Name}`\nDiscord ID: `{websocket.DID}`\nMod Key: `{websocket.Authkey}`\nHWID: `{websocket.HWID}`\n==================",
                    "color": 16761856,
                    "fields": [
                        {"name": "Search Type:", "value": f"`{searchtype}`"},
                        {"name": "Query:", "value": f"`{data}`"},
                        {"name": "Results:", "value": f"`{results}`"},
                    ],
                    "footer": {
                        "text": f"Logged at - {str(await TimeConverter.humanDate(self))}"
                    },
                }
            ],
        }
        await self.loop.create_task(self.request(sender, payload))

    async def avataradded_payload(self, authCheck, data, update=False, ver=None):
        sender = self.BaseVars.AVATAR_WEBHOOK_URL
        tags = (
            json.dumps(data["Tags"], indent=3)
            if data["Tags"] is not None
            else []
        )
        if update is True:
            text = " - Updated Avatar"
            color = 7340287
            version = f"`{ver}` ==> `{data['Version']}`"
        else:
            text = ""
            color = 47103
            version = f"`{data['Version']}`"
        payload = {
            "content": None,
            "embeds": [
                {
                    "title": f"Avatar Added {text}",
                    "description": f"===== [User Info] =====\nDiscord Name: `{authCheck['DiscordName']}`\nDiscord ID: `{authCheck['DiscordID']}`\nMod Key: `{authCheck['AuthKey']}`\nHWID: `{authCheck['HWID']}`\n==================",
                    "color": color,
                    "fields": [
                        {
                            "name": "Avatar ID:",
                            "value": f"`{data['_id']}`",
                        },
                        {
                            "name": "Asset URL:",
                            "value": f"[Download VRCA]({data['AssetURL']})",
                        },
                        {
                            "name": "Author ID:",
                            "value": f"`{data['AuthorID']}`",
                        },
                        {
                            "name": "Author Name:",
                            "value": f"`{data['AuthorName']}`",
                        },
                        {
                            "name": "Avatar Name:",
                            "value": f"`{data['AvatarName']}`",
                        },
                        {
                            "name": "Description:",
                            "value": f"`{data['Description']}`",
                        },
                        {
                            "name": "Featured:",
                            "value": f"`{data['Featured']}`",
                        },
                        {
                            "name": "Image URL:",
                            "value": f"`{data['ImageURL']}`",
                        },
                        {
                            "name": "Release Status:",
                            "value": f"`{data['ReleaseStatus']}`",
                        },
                        {
                            "name": "Supported Platforms:",
                            "value": f"`{data['SupportedPlatforms']}`",
                        },
                        {
                            "name": "Thumbnail Image URL:",
                            "value": f"`{data['ThumbnailImageURL']}`",
                        },
                        {
                            "name": "Tags:",
                            "value": f"`{tags}`",
                        },
                        {
                            "name": "Version:",
                            "value": version,
                        },
                    ],
                    "image": {"url": f"{data['ImageURL']}"},
                    "footer": {
                        "text": f"Logged at - {str(await TimeConverter.humanDate(self))}"
                    },
                }
            ],
        }
        await self.loop.create_task(self.request(sender, payload))

    async def websocket_avataradded_payload(self, websocket, _, update=False, ver=None):
        sender = self.BaseVars.AVATAR_WEBHOOK_URL
        tags = (
            json.dumps(_["payload"]["data"]["Tags"], indent=3)
            if _["payload"]["data"]["Tags"] is not None
            else []
        )
        if update is True:
            text = " - Updated Avatar"
            color = 7340287
            version = f"`{ver}` ==> `{_['payload']['data']['Version']}`"
        else:
            text = ""
            color = 47103
            version = f"`{_['payload']['data']['Version']}`"
        payload = {
            "content": None,
            "embeds": [
                {
                    "title": f"Avatar Added {text}",
                    "description": f"===== [User Info] =====\nDiscord Name: `{websocket.Name}`\nDiscord ID: `{websocket.DID}`\nMod Key: `{websocket.Authkey}`\nHWID: `{websocket.HWID}`\n==================",
                    "color": color,
                    "fields": [
                        {
                            "name": "Avatar ID:",
                            "value": f"`{_['payload']['data']['_id']}`",
                        },
                        {
                            "name": "Asset URL:",
                            "value": f"[Download VRCA]({_['payload']['data']['AssetURL']})",
                        },
                        {
                            "name": "Author ID:",
                            "value": f"`{_['payload']['data']['AuthorID']}`",
                        },
                        {
                            "name": "Author Name:",
                            "value": f"`{_['payload']['data']['AuthorName']}`",
                        },
                        {
                            "name": "Avatar Name:",
                            "value": f"`{_['payload']['data']['AvatarName']}`",
                        },
                        {
                            "name": "Description:",
                            "value": f"`{_['payload']['data']['Description']}`",
                        },
                        {
                            "name": "Featured:",
                            "value": f"`{_['payload']['data']['Featured']}`",
                        },
                        {
                            "name": "Image URL:",
                            "value": f"`{_['payload']['data']['ImageURL']}`",
                        },
                        {
                            "name": "Release Status:",
                            "value": f"`{_['payload']['data']['ReleaseStatus']}`",
                        },
                        {
                            "name": "Supported Platforms:",
                            "value": f"`{_['payload']['data']['SupportedPlatforms']}`",
                        },
                        {
                            "name": "Thumbnail Image URL:",
                            "value": f"`{_['payload']['data']['ThumbnailImageURL']}`",
                        },
                        {
                            "name": "Tags:",
                            "value": f"`{tags}`",
                        },
                        {
                            "name": "Version:",
                            "value": version,
                        },
                    ],
                    "image": {"url": f"{_['payload']['data']['ImageURL']}"},
                    "footer": {
                        "text": f"Logged at - {str(await TimeConverter.humanDate(self))}"
                    },
                }
            ],
        }
        await self.loop.create_task(self.request(sender, payload))

    async def websocket_avataradded_public_payload(self, _, update=False, ver=None):
        sender = self.BaseVars.AVATAR_PUBLIC_WEBHOOK_URL
        tags = (
            json.dumps(_["payload"]["data"]["Tags"], indent=3)
            if _["payload"]["data"]["Tags"] is not None
            else []
        )
        if update is True:
            text = " - Updated Avatar"
            color = 7340287
            version = f"`{ver}` ==> `{_['payload']['data']['Version']}`"
        else:
            text = ""
            color = 47103
            version = f"`{_['payload']['data']['Version']}`"
        payload = {
            "content": None,
            "embeds": [
                {
                    "title": f"Avatar Added {text}",
                    "color": color,
                    "fields": [
                        {
                            "name": "Author ID:",
                            "value": f"`{_['payload']['data']['AuthorID']}`",
                        },
                        {
                            "name": "Author Name:",
                            "value": f"`{_['payload']['data']['AuthorName']}`",
                        },
                        {
                            "name": "Avatar Name:",
                            "value": f"`{_['payload']['data']['AvatarName']}`",
                        },
                        {
                            "name": "Description:",
                            "value": f"`{_['payload']['data']['Description']}`",
                        },
                        {
                            "name": "Featured:",
                            "value": f"`{_['payload']['data']['Featured']}`",
                        },
                        {
                            "name": "Image URL:",
                            "value": f"`{_['payload']['data']['ImageURL']}`",
                        },
                        {
                            "name": "Release Status:",
                            "value": f"`{_['payload']['data']['ReleaseStatus']}`",
                        },
                        {
                            "name": "Supported Platforms:",
                            "value": f"`{_['payload']['data']['SupportedPlatforms']}`",
                        },
                        {
                            "name": "Thumbnail Image URL:",
                            "value": f"`{_['payload']['data']['ThumbnailImageURL']}`",
                        },
                        {
                            "name": "Tags:",
                            "value": f"`{tags}`",
                        },
                        {
                            "name": "Version:",
                            "value": version,
                        },
                    ],
                    "image": {"url": f"{_['payload']['data']['ImageURL']}"},
                    "footer": {
                        "text": f"Logged at - {str(await TimeConverter.humanDate(self))}"
                    },
                }
            ],
        }
        await self.loop.create_task(self.request(sender, payload))

    async def websocket_connect_payload(self, websocket):
        sender = self.BaseVars.WEBSOCKET_WEBHOOK_URL
        payload = {
            "content": f"**[Websocket]** **[Connected]** **[{websocket.SocketType}]** (`{websocket.Name}`) has connected to the websocket with the id (`{websocket.ID}`)"
        }
        await self.loop.create_task(self.request(sender, payload))

    async def websocket_command_payload(self, command_type, websocket, dev_name):
        sender = self.BaseVars.WEBSOCKET_WEBHOOK_URL
        payload = {
            "content": f"**[Websocket]** **[Command]** The command (`{command_type}`) was executed on (`{websocket.Name}`)'s client by (`{dev_name}`)"
        }
        await self.loop.create_task(self.request(sender, payload))

    async def websocket_messageall_payload(self, command_type, clients, dev_name, msg):
        sender = self.BaseVars.WEBSOCKET_WEBHOOK_URL
        payload = {
            "content": f"**[Websocket]** **[Command]** **[Global]** The command (`{command_type}`) was executed on (`{len(clients)}`) clients by (`{dev_name}`), the message contents are: {msg['data']['message']}, message type is: {msg['data']['message_type']}"
        }
        await self.loop.create_task(self.request(sender, payload))

    async def websocket_global_payload(self, command_type, clients, dev_name):
        sender = self.BaseVars.WEBSOCKET_WEBHOOK_URL
        payload = {
            "content": f"**[Websocket]** **[Command]** **[Global]** The command (`{command_type}`) was executed on (`{len(clients)}`) clients by (`{dev_name}`)"
        }
        await self.loop.create_task(self.request(sender, payload))

    async def websocket_disconnect_payload(self, websocket):
        sender = self.BaseVars.WEBSOCKET_WEBHOOK_URL
        payload = {
            "content": f"**[Websocket]** **[Disconnected]** **[{websocket.SocketType}]** (`{websocket.Name}`) has disconnected from the websocket with the id (`{websocket.ID}`)"
        }
        await self.loop.create_task(self.request(sender, payload))

    async def websocket_disconnect_unauthorised_payload(self, websocket):
        sender = self.BaseVars.WEBSOCKET_WEBHOOK_URL
        payload = {
            "content": f"**[Websocket]** **[Disconnected]** **[{websocket.SocketType}]** **[Un-Authorised]** (`{websocket.Name}`) has disconnected from the websocket with the id (`{websocket.ID}`)"
        }
        await self.loop.create_task(self.request(sender, payload))

    async def websocket_disconnect_duplicate_payload(self, websocket):
        sender = self.BaseVars.WEBSOCKET_WEBHOOK_URL
        payload = {
            "content": f"**[Websocket]** **[Disconnected]** **[{websocket.SocketType}]** **[Duplicate Connection]** (`{websocket.Name}`) has disconnected from the websocket with the id (`{websocket.ID}`)"
        }
        await self.loop.create_task(self.request(sender, payload))

    async def websocket_disconnect_banned_payload(self, websocket):
        sender = self.BaseVars.WEBSOCKET_WEBHOOK_URL
        payload = {
            "content": f"**[Websocket]** **[Disconnected]** **[{websocket.SocketType}]** **[Banned]** (`{websocket.Name}`) has disconnected from the websocket with the id (`{websocket.ID}`)"
        }
        await self.loop.create_task(self.request(sender, payload))

    async def websocket_disconnect_hash_payload(self, websocket):
        sender = self.BaseVars.WEBSOCKET_WEBHOOK_URL
        payload = {
            "content": f"**[Websocket]** **[Disconnected]** **[{websocket.SocketType}]** **[UserHash]** (`{websocket.Name}`) has disconnected from the websocket with the id (`{websocket.ID}`)"
        }
        await self.loop.create_task(self.request(sender, payload))

    async def traceback_payload(self, error):
        sender = self.BaseVars.API_TRACEBACK_WEBHOOK_URL
        payload = {
            "content": None,
            "embeds": [
                {
                    "title": "API error detected, traceback below",
                    "description": f"`{error}`",
                    "color": 16716032,
                    "footer": {
                        "text": f"Logged at - {str(await TimeConverter.humanDate(self))}"
                    },
                },
            ],
        }
        await self.loop.create_task(self.request(sender, payload))
