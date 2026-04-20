import os
import logging

# Set BEFORE any Google/OAuth/oauthlib imports
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
os.environ.setdefault("PYDANTIC_DISABLE_PLUGINS", "__all__")

# Enable INFO logging so auth errors are visible in the terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: [%(name)s] %(message)s",
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.database import connect_db, close_db
from app.config.settings import settings
from app.routes import auth, chat, files, integrations

app = FastAPI(
    title="Omni Copilot API",
    description="Unified AI assistant for Google Calendar, Drive, Gmail, and Notion",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(files.router)
app.include_router(integrations.router)


@app.on_event("startup")
async def startup():
    await connect_db()


@app.on_event("shutdown")
async def shutdown():
    await close_db()


@app.get("/")
async def root():
    return {"status": "ok", "service": "Omni Copilot API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
