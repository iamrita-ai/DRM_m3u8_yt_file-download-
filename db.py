from pymongo import MongoClient
import config

mongo = MongoClient(config.MONGO_URL)
db = mongo["serena"]
files = db["files"]


def save_file_record(title: str, file_id: str, is_video: bool):
    if not file_id:
        return
    files.insert_one(
        {
            "title": title,
            "file_id": file_id,
            "is_video": is_video,
        }
    )
