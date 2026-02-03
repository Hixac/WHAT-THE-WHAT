from typing import Any
from datetime import datetime

from pymongo import MongoClient

from src.core.config import settings


class AppData:
    def __init__(self):
        self.client = MongoClient(settings.mongo_url)
        self.db = self.client[settings.MONGO_NAME]
        self.app_data = self.db["app_data"]

    def get(self) -> dict[str, Any]:
        doc = self.app_data.find_one({"app_name": settings.APP_NAME})
        if doc is None:
            doc = {
                "app_name": settings.APP_NAME,
                "frame_index": 5115,
                "datetime": datetime.now()
            }
            _ = self.app_data.insert_one(doc)  # pyright: ignore[reportUnknownMemberType]

        return doc

    def increment_frame_index(self) -> None:
        _ = self.app_data.update_one(
            {"app_name": settings.APP_NAME},
            {
                "$inc": {"frame_index": 1},
                "$set": {"datetime": datetime.now()}
            },
            upsert=False
        )


app_data = AppData()
