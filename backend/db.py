from pymongo import MongoClient, ASCENDING
from datetime import datetime
from typing import List, Dict, Optional
import uuid

# Configure connection
MONGO_URL = "mongodb://127.0.0.1:27017"
client = MongoClient(MONGO_URL)
db = client["ai_assistant"]
sessions_col = db["sessions"]
meta_col = db["meta"]

# Ensure index on session_id for quick lookups
sessions_col.create_index([("session_id", ASCENDING)], unique=True)

Message = Dict[str, str]

def get_messages(session_id: str, limit: Optional[int] = None) -> List[Message]:
    """
    Return messages for a session. If limit is provided, returns the last `limit` messages.
    """
    if limit:
        doc = sessions_col.find_one(
            {"session_id": session_id},
            {"_id": 0, "messages": {"$slice": -limit}}
        )
    else:
        doc = sessions_col.find_one({"session_id": session_id}, {"_id": 0, "messages": 1})

    if not doc:
        return []

    return doc.get("messages", [])

def append_messages(session_id: str, role: str, content: str):
    """
    Append a single message (user/assistant) to session.
    Creates session document if it doesn't exist.
    """
    msg = {
        "role": role,
        "content": content,
        "ts": datetime.utcnow().isoformat(),  # safer for JSON export
    }
    sessions_col.update_one(
        {"session_id": session_id},
        {"$push": {"messages": msg}, "$set": {"last_updated": datetime.utcnow()}},
        upsert=True,
    )

def clear_messages(session_id: str):
    """Clear messages for a session by resetting its array."""
    sessions_col.update_one(
        {"session_id": session_id},
        {"$set": {"messages": [], "last_updated": datetime.utcnow()}},
        upsert=True,
    )

def list_sessions(limit: int = 100) -> List[Dict]:
    """List sessions with metadata (most recent first)."""
    docs = (
        sessions_col.find({}, {"_id": 0, "session_id": 1, "name": 1, "last_updated": 1})
        .sort("last_updated", -1)
        .limit(limit)
    )
    return list(docs)

# ------------------------------
# ✅ Current session tracking
# ------------------------------
def set_current_session(session_id: str):
    """Mark a session_id as the current active session."""
    meta_col.update_one(
        {"_id": "current_session"},
        {"$set": {"session_id": session_id, "updated": datetime.utcnow()}},
        upsert=True,
    )

def get_current_session() -> Optional[str]:
    """Return the currently active session_id, or None if not set."""
    doc = meta_col.find_one({"_id": "current_session"})
    return doc.get("session_id") if doc else None
