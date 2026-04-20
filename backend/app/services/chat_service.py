import uuid
import json
from datetime import datetime, timezone
from typing import Optional
from app.config.database import get_db
from app.models.schemas import ChatSession, Message
from app.services.ai_service import call_groq_with_tools
from app.utils.encryption import decrypt_token


def _bson_safe(obj):
    """Recursively convert non-serializable objects to plain Python dicts/lists."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return {k: _bson_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_bson_safe(i) for i in obj]
    if hasattr(obj, "items"):
        return {k: _bson_safe(v) for k, v in obj.items()}
    if hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
        try:
            return [_bson_safe(i) for i in obj]
        except Exception:
            pass
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


async def get_or_create_session(user_id: str, session_id: Optional[str] = None) -> dict:
    db = get_db()
    if session_id:
        session = await db.sessions.find_one({"session_id": session_id, "user_id": user_id})
        if session:
            return session

    new_session = {
        "session_id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": "New Chat",
        "messages": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    await db.sessions.insert_one(new_session)
    return new_session


async def list_sessions(user_id: str) -> list:
    db = get_db()
    cursor = db.sessions.find(
        {"user_id": user_id},
        {"session_id": 1, "title": 1, "updated_at": 1, "messages": {"$slice": -1}},
    ).sort("updated_at", -1).limit(20)
    sessions = []
    async for s in cursor:
        s.pop("_id", None)
        sessions.append(s)
    return sessions


async def delete_session(user_id: str, session_id: str) -> bool:
    """Delete a chat session for a given user. Returns True if deleted."""
    db = get_db()
    result = await db.sessions.delete_one({"session_id": session_id, "user_id": user_id})
    return result.deleted_count > 0


async def send_message(
    user_id: str,
    session_id: str,
    message: str,
    file_context: Optional[str] = None,
) -> dict:
    db = get_db()
    session = await get_or_create_session(user_id, session_id)
    actual_session_id = session["session_id"]

    user = await db.users.find_one({"user_id": user_id})
    google_token_data = None
    notion_token = None

    if user:
        integrations = user.get("integrations", {})
        enc_google = integrations.get("google_token")
        enc_notion = integrations.get("notion_token")
        if enc_google:
            try:
                google_token_data = json.loads(decrypt_token(enc_google))
            except Exception:
                pass
        if enc_notion:
            try:
                notion_token = decrypt_token(enc_notion)
            except Exception:
                pass

    history = [
        {"role": m["role"], "content": m["content"]}
        for m in session.get("messages", [])
    ]

    user_msg = {
        "role": "user",
        "content": message,
        "timestamp": datetime.now(timezone.utc),
    }

    ai_result = call_groq_with_tools(
        user_message=message,
        conversation_history=history,
        google_token_data=google_token_data,
        notion_token=notion_token,
        file_context=file_context,
    )

    ai_response = ai_result["response"]
    tool_trace = _bson_safe(ai_result.get("tool_trace", []))

    assistant_msg = {
        "role": "assistant",
        "content": ai_response,
        "timestamp": datetime.now(timezone.utc),
        "tool_trace": tool_trace,
    }

    # FIX: Use a single atomic update — no duplicate $push
    title_set = {}
    if not session.get("messages"):
        title_set["title"] = message[:60] + ("..." if len(message) > 60 else "")

    await db.sessions.update_one(
        {"session_id": actual_session_id},
        {
            "$set": {**title_set, "updated_at": datetime.now(timezone.utc)},
            "$push": {"messages": {"$each": [user_msg, assistant_msg]}},
        },
    )

    return {
        "session_id": actual_session_id,
        "message": ai_response,
        "tool_trace": tool_trace,
    }


async def get_session_messages(user_id: str, session_id: str) -> list:
    db = get_db()
    session = await db.sessions.find_one(
        {"session_id": session_id, "user_id": user_id}
    )
    if not session:
        return []
    messages = session.get("messages", [])
    for m in messages:
        m.pop("_id", None)
        if isinstance(m.get("timestamp"), datetime):
            m["timestamp"] = m["timestamp"].isoformat()
    return messages
