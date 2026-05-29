from datetime import datetime, timezone
from bson import ObjectId


def make_task(user_id: str, name: str, deadline: str, description: str) -> dict:
    return {
        "user_id": ObjectId(user_id),
        "name": name,
        "deadline": deadline,   # stored as "YYYY-MM-DD" string
        "description": description,
        "created_at": datetime.now(timezone.utc),
    }
