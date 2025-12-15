"""
FastAPI application entry point.
"""
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from app.websocket import websocket_endpoint

# Create FastAPI app
app = FastAPI(
    title="Real-Time AI Conversation Backend",
    description="WebSocket-based AI conversation system with Supabase persistence",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Real-Time AI Conversation Backend",
        "version": "1.0.0",
        "websocket_endpoint": "/ws/session/{session_id}"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.websocket("/ws/session/{session_id}")
async def websocket_route(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time AI conversations.
    
    Args:
        websocket: WebSocket connection
        session_id: Unique session identifier
    """
    await websocket_endpoint(websocket, session_id)


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    print("🚀 Real-Time AI Conversation Backend started")
    print("📡 WebSocket endpoint: /ws/session/{session_id}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    print("👋 Shutting down Real-Time AI Conversation Backend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
