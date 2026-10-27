import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "test_ai")

if not MONGO_URL:
    raise RuntimeError(
        "MONGO_URL is not configured in backend/.env"
    )

client = MongoClient(MONGO_URL)

db = client[DATABASE_NAME]

users_collection = db["users"]
projects_collection = db["projects"]
test_cases_collection = db["test_cases"]
test_runs_collection = db["test_runs"]


def check_database():
    try:
        client.admin.command("ping")
        return True
    except Exception:
        return False