from fastapi import APIRouter, HTTPException, Query
from app.config.database import get_db
from app.utils.encryption import decrypt_token
import json

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.get("/status/{user_id}")
async def get_integration_status(user_id: str):
    db = get_db()
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    integrations = user.get("integrations", {})
    return {
        "google_connected": integrations.get("google_connected", False),
        "notion_connected": integrations.get("notion_connected", False),
    }
