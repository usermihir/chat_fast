"""
Post-session processing: Generate summary and update session metadata.
"""
import asyncio
from datetime import datetime
from typing import List, Dict
from app.db import get_db
from app.llm import get_llm_handler
from app.models import SessionUpdate


async def process_session_summary(session_id: str) -> None:
    """
    Background job to summarize conversation and update session.
    
    This runs asynchronously after WebSocket disconnect:
    1. Fetch all events from database
    2. Generate summary using LLM
    3. Calculate session duration
    4. Update session record
    
    Args:
        session_id: Session to process
    """
    try:
        # Fetch session metadata
        session = await get_db().get_session(session_id)
        if not session:
            print(f"Session {session_id} not found")
            return
        
        # Fetch all conversation events
        events = await get_db().get_session_events(session_id)
        
        if not events:
            print(f"No events found for session {session_id}")
            return
        
        # Build conversation history for summarization
        messages = []
        for event in events:
            # Skip tool-specific events in summary
            if event.role in ["user", "assistant", "system"]:
                messages.append({
                    "role": event.role,
                    "content": event.content
                })
        
        # Generate summary
        print(f"Generating summary for session {session_id}...")
        summary = await get_llm_handler().generate_summary(messages)
        
        # Calculate duration with timezone-aware datetimes
        from datetime import timezone
        end_time = datetime.now(timezone.utc)
        start_time = session.get("start_time")
        
        # Parse start_time if it's a string
        if isinstance(start_time, str):
            # Remove timezone suffix and parse, then make it timezone-aware
            start_time_str = start_time.replace('+00:00', '').replace('Z', '')
            start_time = datetime.fromisoformat(start_time_str).replace(tzinfo=timezone.utc)
        elif not start_time.tzinfo:
            # If start_time is naive, make it timezone-aware
            start_time = start_time.replace(tzinfo=timezone.utc)
        
        duration_seconds = int((end_time - start_time).total_seconds())
        
        # Update session
        update = SessionUpdate(
            end_time=end_time,
            duration_seconds=duration_seconds,
            summary=summary
        )
        
        await get_db().update_session(session_id, update)
        
        print(f"Session {session_id} summary complete: {duration_seconds}s, summary: {summary[:100]}...")
        
    except Exception as e:
        print(f"Error processing session summary for {session_id}: {str(e)}")


def trigger_summary_job(session_id: str) -> asyncio.Task:
    """
    Trigger async summary job without blocking.
    
    Args:
        session_id: Session to summarize
        
    Returns:
        Async task handle
    """
    return asyncio.create_task(process_session_summary(session_id))
