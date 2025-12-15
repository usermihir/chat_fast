"""
Database models and Pydantic schemas for type-safe operations.
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Schema for creating a new session."""
    session_id: str
    user_id: Optional[str] = None


class SessionUpdate(BaseModel):
    """Schema for updating session metadata."""
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    summary: Optional[str] = None


class EventCreate(BaseModel):
    """Schema for creating a new event."""
    session_id: str
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None


class Event(BaseModel):
    """Schema for event retrieval."""
    id: int
    session_id: str
    role: str
    content: str
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Session(BaseModel):
    """Schema for session retrieval."""
    session_id: str
    user_id: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages from client."""
    type: Literal["message", "ping"]
    content: Optional[str] = None


class WebSocketResponse(BaseModel):
    """Schema for WebSocket responses to client."""
    type: Literal["token", "error", "done", "tool_call", "pong"]
    content: Optional[str] = None
    tool_name: Optional[str] = None
    tool_result: Optional[str] = None
