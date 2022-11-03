import json
import sys
import base64
from Libs.Logger import Logger
from Libs.ConnectionManager import ConnectionManager
from motor.motor_asyncio import AsyncIOMotorClient as MotorClient

sys.setrecursionlimit(100000)


class baseVars(object):
    log = Logger()
    ConnectionManager = ConnectionManager()
    with open("config.json", "r", encoding="utf-8") as f:
        CONFIG_DATA: dict = json.loads(f.read())
        AVATAR_WEBHOOK_URL: str = CONFIG_DATA["data"][0]["webhooks"]["avatar_webhook"]
        AVATAR_PUBLIC_WEBHOOK_URL: str = CONFIG_DATA["data"][0]["webhooks"][
            "avatar_public_webhook"
        ]
        SEARCH_AVATAR_WEBHOOK_URL: str = CONFIG_DATA["data"][0]["webhooks"][
            "search_avatar_webhook"
        ]
        USER_WEBHOOK_URL: str = CONFIG_DATA["data"][0]["webhooks"]["user_webhook"]
        WEBSOCKET_WEBHOOK_URL: str = CONFIG_DATA["data"][0]["webhooks"][
            "websocket_webhook"
        ]
        API_TRACEBACK_WEBHOOK_URL: str = CONFIG_DATA["data"][0]["webhooks"][
            "apitraceback_webhook"
        ]
        API_REQUEST_WEBHOOK_URL: str = CONFIG_DATA["data"][0]["webhooks"][
            "apirequest_webhook"
        ]
        REGISTRY_LOGS_WEBHOOK_URL: str = CONFIG_DATA["data"][0]["webhooks"][
            "registry_webhook"
        ]
        DB_KEY: str = base64.b64decode(CONFIG_DATA["data"][0]["dbKey"]).decode("utf-8")
        RANDO_HEADERS: list = CONFIG_DATA["data"][0]["header_array"]
        LOADER_VERSION: str = CONFIG_DATA["data"][0]["loader_version"]
        CLIENT_VERSION: str = CONFIG_DATA["data"][0]["client_version"]
        FASTAPI_CONFIG: dict = CONFIG_DATA["data"][0]["server_config"]
        MIDDLE_WARE: str = CONFIG_DATA["data"][0]["middle_ware"]

    log.info("Creating database object")
    try:
        db = MotorClient(DB_KEY)
    except Exception as e:
        log.error(f"Database object couldn't be started: {e}")
        exit()

    dynamic_lists = {}
