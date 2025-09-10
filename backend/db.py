from pymongo import MongoClient, ASCENDING
from datetime import datetime
from typing import List, Dict, Optional

# Configure connection
MONGO_URL = "mongodb://127.0.0.1:27017"
client = MongoClient(MONGO_URL)
db = client["ai_assistant"]
sessions_col = db["sessions"]


# Ensure index on session_id for quick lookups
sessions_col.create_index([("session_id", ASCENDING)], unique=True)

Message = Dict[str, str]


def get_messages(session_id: str, limit: Optional[int] = None) -> List[Message]:
    """
    Return messages for a session. If limit is provided, returns the last `limit` messages.
    """
    if limit:
        doc = sessions_col.find_one(
            {"session_id": session_id}, {"messages": {"$slice": -limit}}
        )
    else:
        doc = sessions_col.find_one({"session_id": session_id})

    if not doc:
        return []
    return doc.get("messages", [])


def append_messages(session_id: str, role: str, content: str):
    """
    Append a single message (user/assistant) to session.
    Creates session document if it doesn't exist.
    """
    msg = {"role": role, "content": content, "ts": datetime.utcnow()}
    sessions_col.update_one(
        {"session_id": session_id},
        {"$push": {"messages": msg}, "$set": {"last_updated": datetime.utcnow()}},
        upsert=True,
    )


def reset_session(session_id: str):
    """
    Clear message for a session. (Either delete doc or set empty array)
    """
    sessions_col.update_one(
        {"session_id": session_id},
        {"$set": {"messages": [], "last_updated": datetime.utcnow()}},
        upsert=True,
    )


def list_sessions(limit: int = 50) -> List[Dict]:
    """Return recent sessions' metadata."""
    docs = (
        sessions_col.find({}, {"session_id": 1, "last_updated": 1})
        .sort("last_updated", -1)
        .limit(limit)
    )
    return list(docs)
