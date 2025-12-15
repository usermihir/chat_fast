"""
Supabase database client with async operations.
"""
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

from app.models import SessionCreate, SessionUpdate, EventCreate, Event

# Load environment variables
load_dotenv()


class Database:
    """Async Supabase database client."""
    
    _instance = None
    
    def __init__(self):
        """Initialize Supabase client."""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
        
        self.client: Client = create_client(supabase_url, supabase_key)
    
    async def create_session(self, session: SessionCreate) -> Dict[str, Any]:
        """
        Create a new session in the database.
        
        Args:
            session: Session creation data
            
        Returns:
            Created session data
        """
        try:
            result = self.client.table("sessions").insert({
                "session_id": session.session_id,
                "user_id": session.user_id,
                "start_time": datetime.utcnow().isoformat()
            }).execute()
            
            return result.data[0] if result.data else {}
        except Exception as e:
            raise Exception(f"Failed to create session: {str(e)}")
    
    async def update_session(self, session_id: str, update: SessionUpdate) -> Dict[str, Any]:
        """
        Update session metadata.
        
        Args:
            session_id: Session identifier
            update: Update data
            
        Returns:
            Updated session data
        """
        try:
            update_data = {}
            if update.end_time:
                update_data["end_time"] = update.end_time.isoformat()
            if update.duration_seconds is not None:
                update_data["duration_seconds"] = update.duration_seconds
            if update.summary:
                update_data["summary"] = update.summary
            
            result = self.client.table("sessions").update(update_data).eq(
                "session_id", session_id
            ).execute()
            
            return result.data[0] if result.data else {}
        except Exception as e:
            raise Exception(f"Failed to update session: {str(e)}")
    
    async def insert_event(self, event: EventCreate) -> Dict[str, Any]:
        """
        Insert a new event (message) into the database.
        
        Args:
            event: Event data
            
        Returns:
            Created event data
        """
        try:
            event_data = {
                "session_id": event.session_id,
                "role": event.role,
                "content": event.content
            }
            
            if event.tool_call_id:
                event_data["tool_call_id"] = event.tool_call_id
            if event.tool_name:
                event_data["tool_name"] = event.tool_name
            
            result = self.client.table("events").insert(event_data).execute()
            
            return result.data[0] if result.data else {}
        except Exception as e:
            raise Exception(f"Failed to insert event: {str(e)}")
    
    async def get_session_events(self, session_id: str) -> List[Event]:
        """
        Retrieve all events for a session, ordered by creation time.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of events
        """
        try:
            result = self.client.table("events").select("*").eq(
                "session_id", session_id
            ).order("created_at", desc=False).execute()
            
            return [Event(**event) for event in result.data]
        except Exception as e:
            raise Exception(f"Failed to get session events: {str(e)}")
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session metadata.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None
        """
        try:
            result = self.client.table("sessions").select("*").eq(
                "session_id", session_id
            ).execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            raise Exception(f"Failed to get session: {str(e)}")


# Lazy database initialization
_db_instance = None

def get_db() -> Database:
    """Get or create database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance

# For backward compatibility
db = None
