# Quick Start Guide

## Prerequisites Check

Before running the application, ensure you have:

1. ✅ Python 3.9+ installed
2. ✅ Supabase account created
3. ✅ OpenAI API key

## Step 1: Database Setup

1. Log into your Supabase project at https://supabase.com
2. Go to **SQL Editor**
3. Copy and paste the contents of `schema.sql`
4. Click **Run** to create the tables

## Step 2: Configure Environment

1. Open the `.env` file in the project root
2. Replace the placeholder values:

```env
SUPABASE_URL=https://your-actual-project-id.supabase.co
SUPABASE_KEY=your-actual-anon-key-from-supabase
OPENAI_API_KEY=sk-your-actual-openai-api-key
```

**Where to find these values:**
- **SUPABASE_URL**: Supabase Dashboard → Settings → API → Project URL
- **SUPABASE_KEY**: Supabase Dashboard → Settings → API → Project API keys → anon/public
- **OPENAI_API_KEY**: https://platform.openai.com/api-keys

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 4: Start the Backend

```bash
uvicorn app.main:app --reload
```

You should see:
```
🚀 Real-Time AI Conversation Backend started
📡 WebSocket endpoint: /ws/session/{session_id}
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## Step 5: Test the Application

1. Open `frontend/index.html` in your web browser
2. You should see "Connected" with a green dot
3. Type a message and press Enter
4. Watch the AI response stream in real-time!

## Testing Function Calling

Ask: **"What time is it?"**

You'll see:
1. 🔧 Tool call notification
2. ✓ Tool result with current time
3. AI's natural language response

## Verify Database Persistence

1. Open Supabase Dashboard → Table Editor
2. Check the `events` table - you should see your messages
3. Close the browser tab
4. Wait 5-10 seconds
5. Check the `sessions` table - you should see a summary!

## Troubleshooting

**"SUPABASE_URL must be set"**
→ Make sure `.env` file exists and has correct values

**"WebSocket won't connect"**
→ Ensure backend is running on port 8000

**"No response from AI"**
→ Check your OpenAI API key and billing status

---

**Need help?** Check the full README.md for detailed documentation.
