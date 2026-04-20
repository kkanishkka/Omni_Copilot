from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone


class UserIntegrations(BaseModel):
    google_connected: bool = False
    notion_connected: bool = False
    google_token: Optional[str] = None
    notion_token: Optional[str] = None


class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    integrations: UserIntegrations = UserIntegrations()
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def model_dump(self, **kwargs):
        return super().model_dump(**kwargs)


class Message(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tool_trace: Optional[List[Dict[str, Any]]] = None


class ChatSession(BaseModel):
    session_id: str
    user_id: str
    title: str = "New Chat"
    messages: List[Message] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str
    file_context: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    message: str
    tool_trace: Optional[List[Dict[str, Any]]] = None


class NotionConnectRequest(BaseModel):
    user_id: str
    token: str


class ToolTrace(BaseModel):
    tool_name: str
    input: Dict[str, Any]
    output: Optional[Any] = None
    status: str = "pending"  # pending | success | error
    duration_ms: Optional[int] = None
