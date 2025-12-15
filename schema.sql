-- Real-Time AI Conversation Backend - Database Schema
-- Execute this in your Supabase SQL Editor

-- Table: sessions
-- Stores high-level session metadata and lifecycle information
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT,
    start_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    end_time TIMESTAMPTZ,
    duration_seconds INTEGER,
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: events
-- Stores individual messages and assistant responses
CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT NOT NULL,
    tool_call_id TEXT,
    tool_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_events_session_id ON events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time);

-- Comments for documentation
COMMENT ON TABLE sessions IS 'Stores conversation session metadata and AI-generated summaries';
COMMENT ON TABLE events IS 'Stores individual messages, assistant responses, and tool calls';
COMMENT ON COLUMN events.role IS 'Message role: user, assistant, system, or tool';
COMMENT ON COLUMN events.tool_call_id IS 'ID for tool call responses (when role=tool)';
COMMENT ON COLUMN events.tool_name IS 'Name of the tool that was called';
