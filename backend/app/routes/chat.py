from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest
from app.services.chat_service import (
    send_message,
    list_sessions,
    get_session_messages,
    get_or_create_session,
    delete_session,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/send")
async def chat_send(req: ChatRequest):
    try:
        result = await send_message(
            user_id=req.user_id,
            session_id=req.session_id,
            message=req.message,
            file_context=req.file_context,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{user_id}")
async def get_sessions(user_id: str):
    sessions = await list_sessions(user_id)
    return {"sessions": sessions}


@router.get("/messages/{user_id}/{session_id}")
async def get_messages(user_id: str, session_id: str):
    messages = await get_session_messages(user_id, session_id)
    return {"messages": messages}


@router.post("/sessions/{user_id}")
async def create_session(user_id: str):
    session = await get_or_create_session(user_id)
    return {"session_id": session["session_id"]}


@router.delete("/sessions/{user_id}/{session_id}")
async def delete_chat_session(user_id: str, session_id: str):
    """Delete a specific chat session."""
    deleted = await delete_session(user_id, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True, "session_id": session_id}
