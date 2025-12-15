"""
WebSocket handler for real-time AI conversations.
"""
import json
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect
from app.db import get_db
from app.llm import get_llm_handler
from app.models import SessionCreate, EventCreate, WebSocketMessage
from app.post_session import trigger_summary_job


class ConnectionManager:
    """Manages WebSocket connections and conversation state."""
    
    def __init__(self):
        """Initialize connection manager."""
        # Store active connections and their conversation history
        self.active_connections: Dict[str, WebSocket] = {}
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """
        Accept WebSocket connection and initialize session.
        
        Args:
            websocket: WebSocket connection
            session_id: Unique session identifier
        """
        await websocket.accept()
        self.active_connections[session_id] = websocket
        
        # Initialize conversation with system message
        self.conversation_history[session_id] = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant. You have access to tools that you can use to help answer questions."
            }
        ]
        
        # Create session in database
        try:
            session = SessionCreate(session_id=session_id, user_id=None)
            await get_db().create_session(session)
            print(f"Session {session_id} created")
        except Exception as e:
            print(f"Error creating session: {str(e)}")
    
    def disconnect(self, session_id: str):
        """
        Remove connection and trigger post-session processing.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
        
        # Trigger async summary job
        trigger_summary_job(session_id)
        print(f"Session {session_id} disconnected, summary job triggered")
    
    async def handle_message(self, session_id: str, message: str):
        """
        Process user message and stream LLM response.
        
        Args:
            session_id: Session identifier
            message: User message content
        """
        websocket = self.active_connections.get(session_id)
        if not websocket:
            return
        
        try:
            # Add user message to history
            self.conversation_history[session_id].append({
                "role": "user",
                "content": message
            })
            
            # Save user message to database
            user_event = EventCreate(
                session_id=session_id,
                role="user",
                content=message
            )
            await get_db().insert_event(user_event)
            
            # Stream LLM response
            assistant_message = ""
            tool_responses = []
            
            async for event in get_llm_handler().stream_completion(
                self.conversation_history[session_id],
                session_id
            ):
                event_type = event.get("type")
                
                if event_type == "token":
                    # Stream token to client
                    content = event.get("content", "")
                    assistant_message += content
                    await websocket.send_json({
                        "type": "token",
                        "content": content
                    })
                
                elif event_type == "tool_call":
                    # Notify client about tool call
                    await websocket.send_json({
                        "type": "tool_call",
                        "tool_name": event.get("tool_name"),
                        "tool_id": event.get("tool_id")
                    })
                
                elif event_type == "tool_result":
                    # Send tool result to client
                    tool_name = event.get("tool_name")
                    tool_content = event.get("content")
                    tool_responses.append({
                        "tool_name": tool_name,
                        "content": tool_content
                    })
                    
                    await websocket.send_json({
                        "type": "tool_result",
                        "tool_name": tool_name,
                        "content": tool_content
                    })
                    
                    # Save tool result to database
                    tool_event = EventCreate(
                        session_id=session_id,
                        role="tool",
                        content=tool_content,
                        tool_name=tool_name
                    )
                    await get_db().insert_event(tool_event)
                
                elif event_type == "error":
                    # Send error to client
                    await websocket.send_json({
                        "type": "error",
                        "content": event.get("content", "Unknown error")
                    })
                    return
                
                elif event_type == "done":
                    # Streaming complete
                    await websocket.send_json({"type": "done"})
            
            # Add assistant message to history
            if assistant_message:
                self.conversation_history[session_id].append({
                    "role": "assistant",
                    "content": assistant_message
                })
                
                # Save assistant message to database
                assistant_event = EventCreate(
                    session_id=session_id,
                    role="assistant",
                    content=assistant_message
                )
                await get_db().insert_event(assistant_event)
        
        except Exception as e:
            print(f"Error handling message: {str(e)}")
            try:
                await websocket.send_json({
                    "type": "error",
                    "content": f"Error processing message: {str(e)}"
                })
            except:
                pass


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time conversations.
    
    Lifecycle:
    1. Accept connection and create session
    2. Receive user messages and stream responses
    3. On disconnect, trigger summary job
    
    Args:
        websocket: WebSocket connection
        session_id: Unique session identifier
    """
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                msg = WebSocketMessage(**message_data)
                
                if msg.type == "message" and msg.content:
                    await manager.handle_message(session_id, msg.content)
                
                elif msg.type == "ping":
                    await websocket.send_json({"type": "pong"})
            
            except json.JSONDecodeError:
                # Treat as plain text message
                await manager.handle_message(session_id, data)
            
            except Exception as e:
                print(f"Error processing message: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "content": f"Invalid message format: {str(e)}"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        manager.disconnect(session_id)
