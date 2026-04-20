import json
import logging
import urllib.parse
from fastapi import APIRouter, Query, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.config.database import get_db
from app.config.settings import settings
from app.integrations.google_auth import get_google_auth_url, handle_google_callback
from app.utils.encryption import encrypt_token
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/google/login")
async def google_login(user_id: str = Query("new")):
    auth_url = get_google_auth_url(user_id)
    return {"auth_url": auth_url}


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
):
    if error:
        logger.warning(f"[OAuth] Google returned error: {error}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}?error={urllib.parse.quote(error)}",
            status_code=302,
        )

    if not code:
        logger.warning("[OAuth] Callback received with no code param")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}?error=no_code",
            status_code=302,
        )

    # Log the incoming URL (helps debug host/scheme issues on Windows)
    raw_url = str(request.url)
    logger.info(f"[OAuth] Callback raw URL: {raw_url}")

    try:
        profile, token_data = handle_google_callback(
            code=code,
            state=state,
            request_url=raw_url,
        )
    except Exception as e:
        logger.error(f"[OAuth] Token exchange failed: {e}", exc_info=True)
        err_msg = urllib.parse.quote(str(e))
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}?error={err_msg}",
            status_code=302,
        )

    db = get_db()
    user_id = profile.get("id") or profile.get("sub")
    email = profile.get("email", "")
    name = profile.get("name", "User")
    picture = profile.get("picture", "")

    logger.info(f"[OAuth] Login success for {email} (user_id={user_id})")

    encrypted_token = encrypt_token(json.dumps(token_data))

    await db.users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "email": email,
                "name": name,
                "picture": picture,
                "integrations.google_connected": True,
                "integrations.google_token": encrypted_token,
                "updated_at": datetime.now(timezone.utc),
            },
            "$setOnInsert": {
                "created_at": datetime.now(timezone.utc),
            },
        },
        upsert=True,
    )

    redirect_url = (
        f"{settings.FRONTEND_URL}/auth/success"
        f"?user_id={user_id}"
        f"&email={urllib.parse.quote(email)}"
        f"&name={urllib.parse.quote(name)}"
        f"&picture={urllib.parse.quote(picture)}"
    )
    return RedirectResponse(url=redirect_url, status_code=302)


@router.get("/profile/{user_id}")
async def get_profile(user_id: str):
    db = get_db()
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.pop("_id", None)
    if "integrations" in user:
        user["integrations"].pop("google_token", None)
        user["integrations"].pop("notion_token", None)
    return user


@router.post("/notion/connect")
async def notion_connect(user_id: str = Query(...), token: str = Query(...)):
    db = get_db()
    encrypted_token = encrypt_token(token)
    await db.users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "integrations.notion_connected": True,
                "integrations.notion_token": encrypted_token,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    return {"status": "success", "message": "Notion connected"}


@router.delete("/notion/disconnect/{user_id}")
async def notion_disconnect(user_id: str):
    db = get_db()
    await db.users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "integrations.notion_connected": False,
                "integrations.notion_token": None,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    return {"status": "success", "message": "Notion disconnected"}
