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


def create_session(session_id: Optional[str] = None, name: Optional[str] = None, make_current: bool = False) -> str:
    """
    Create a new session doc (or ensure it exists). Returns session_id.
    If make_current=True, sets this session as the current session in the meta collection.
    """
    sid = session_id or uuid.uuid4().hex
    now = datetime.utcnow()
    sessions_col.update_one(
        {"session_id": sid},
        {
            "$setOnInsert": {
                "session_id": sid,
                "name": name or "",
                "messages": [],
                "created_at": now,
                "last_updated": now,
            }
        },
        upsert=True,
    )
    if make_current:
        set_current_session(sid)
    return sid


def get_current_session() -> Optional[str]:
    """Return the currently active session_id, or None if not set."""
    doc = meta_col.find_one({"_id": "current_session"})
    return doc.get("session_id") if doc else None


def set_current_session(session_id: str):
    """Mark a session_id as the current active session."""
    meta_col.update_one(
        {"_id": "current_session"},
        {"$set": {"session_id": session_id, "updated": datetime.utcnow()}},
        upsert=True,
    )


def session_exists(session_id: str) -> bool:
    """Return True if a session with session_id exists in sessions collection."""
    return sessions_col.count_documents({"session_id": session_id}, limit=1) > 0


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
        "ts": datetime.utcnow().isoformat(),  # ISO string is handy for JSON
    }
    sessions_col.update_one(
        {"session_id": session_id},
        {
            "$push": {"messages": msg},
            "$set": {"last_updated": datetime.utcnow()},
        },
        upsert=True,
    )


def clear_messages(session_id: str) -> bool:
    """
    Clear messages for a session (preserves the session doc).
    Returns True if a document was matched and cleared, False if no session existed.
    NOTE: upsert=False -> we will NOT create a session when clearing.
    """
    res = sessions_col.update_one(
        {"session_id": session_id},
        {"$set": {"messages": [], "last_updated": datetime.utcnow()}},
        upsert=False,
    )
    return res.matched_count > 0


def list_sessions(limit: int = 100) -> List[Dict]:
    """
    Return recent sessions' metadata (no messages included).
    """
    docs = sessions_col.find({}, {"_id": 0, "session_id": 1, "name": 1, "last_updated": 1}).sort("last_updated", -1).limit(limit)
    return list(docs)
