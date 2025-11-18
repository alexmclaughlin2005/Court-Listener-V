# Streaming Response Debugging Guide

## Issue
AI analysis streaming is not working - all text appears at once instead of incrementally.

## Root Cause Analysis

### Confirmed Working
- Backend streaming with curl works ✅ (chunks arrive individually)
- Frontend SSE parsing code is correct ✅
- React updates with flushSync() ✅

### Likely Issue: Network Buffering

The problem is **response buffering** happening between Railway (backend) and the browser. Possible buffering locations:

1. **Vercel Edge Network** - Most likely culprit
2. **Browser HTTP stack** - Less likely (SSE should bypass this)
3. **Railway proxy** - Already addressed with `X-Accel-Buffering: no`

## Why Vercel Buffers Streaming

When the frontend (deployed on Vercel) makes requests to Railway backend:
```
Browser → Vercel Edge → Railway Backend → Anthropic API
        ↓ BUFFERING HERE
```

Vercel's edge network may buffer responses for:
- Performance optimization
- Response compression
- Error handling
- CDN caching

## Testing Steps

### 1. Test Direct Backend Connection (Bypass Vercel)

Open browser console and run:
```javascript
const response = await fetch('https://court-listener-v-production.up.railway.app/api/v1/ai-analysis/403793?quick=true', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' }
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value, { stream: true });
  console.log(`[${new Date().toISOString()}] Chunk:`, chunk.substring(0, 50));
}
```

**Expected Result**:
- If chunks arrive at different timestamps → Backend is streaming correctly
- If one big chunk arrives → Backend issue

### 2. Check Network Tab Timing

1. Open Chrome DevTools → Network tab
2. Trigger AI analysis
3. Find the `/api/v1/ai-analysis/` request
4. Click on it and check the "Timing" tab

**What to look for**:
- **Waiting (TTFB)**: Time until first byte
- **Content Download**: Should be 10-30s for streaming (not <1s)

If Content Download is very short → Response was buffered and sent all at once.

### 3. Test Localhost Development Server

Run frontend locally pointing to production backend:
```bash
cd frontend
# Edit .env to use production backend
echo "VITE_API_URL=https://court-listener-v-production.up.railway.app" > .env.local
npm run dev
```

Then test the streaming. If it works locally but not on Vercel → Vercel is buffering.

## Solutions

### Solution 1: Add Vercel API Proxy with Streaming (Recommended)

Create `frontend/api/stream/[...path].ts`:
```typescript
import { NextRequest } from 'next/server';

export const config = {
  runtime: 'edge',
};

export default async function handler(req: NextRequest) {
  const url = new URL(req.url);
  const path = url.pathname.replace('/api/stream/', '');

  const backendUrl = `https://court-listener-v-production.up.railway.app/api/v1/${path}${url.search}`;

  const response = await fetch(backendUrl, {
    method: req.method,
    headers: {
      'Content-Type': 'application/json',
    },
    body: req.method === 'POST' ? await req.text() : undefined,
  });

  return new Response(response.body, {
    status: response.status,
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}
```

Update `frontend/src/lib/api.ts`:
```typescript
// Change from:
const url = `${API_URL}/api/v1/ai-analysis/${opinionId}${params}`;

// To:
const url = `/api/stream/ai-analysis/${opinionId}${params}`;
```

### Solution 2: Use WebSocket Instead of SSE

WebSocket connections are bidirectional and won't be buffered by proxies.

**Backend** (`backend/app/api/v1/ai_analysis_ws.py`):
```python
from fastapi import WebSocket

@router.websocket("/ws/ai-analysis/{opinion_id}")
async def analyze_opinion_ws(websocket: WebSocket, opinion_id: int):
    await websocket.accept()

    # ... get opinion data ...

    stream_generator = await analyzer.analyze_citation_risk(...)

    for chunk in stream_generator:
        if isinstance(chunk, dict):
            await websocket.send_json(chunk)
        else:
            await websocket.send_json({'type': 'text', 'content': chunk})

    await websocket.send_json({'type': 'done'})
    await websocket.close()
```

**Frontend**:
```typescript
const ws = new WebSocket('wss://court-listener-v-production.up.railway.app/ws/ai-analysis/403793');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'text') {
    onChunk(data.content);
  }
};
```

### Solution 3: Update Vercel Configuration

Add to `vercel.json`:
```json
{
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "no-cache, no-store, must-revalidate" },
        { "key": "X-Accel-Buffering", "value": "no" }
      ]
    }
  ]
}
```

This won't help if Vercel buffers before checking headers, but worth trying.

### Solution 4: Deploy Frontend to Railway (Quick Test)

Deploy the frontend to Railway alongside the backend to eliminate Vercel from the equation:

```bash
cd frontend
# Add to package.json scripts:
"serve": "vite preview --host 0.0.0.0 --port $PORT"
```

Create `frontend/Dockerfile`:
```dockerfile
FROM node:18-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "serve"]
```

## Recommended Action Plan

1. **First**: Test direct backend connection in browser console (Testing Step 1)
2. **If that works**: Deploy with Solution 1 (Vercel API proxy)
3. **If still doesn't work**: Switch to Solution 2 (WebSocket)

## Additional Backend Debugging

Add explicit flushing to `backend/app/api/v1/ai_analysis.py`:

```python
import asyncio

async def generate():
    # Send initial metadata
    initial_data = {...}
    yield f"data: {json.dumps(initial_data)}\n\n"
    await asyncio.sleep(0)  # Force flush

    # Stream text chunks
    for chunk in stream_generator:
        if isinstance(chunk, dict):
            yield f"data: {json.dumps(chunk)}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"
        await asyncio.sleep(0)  # Force flush after each chunk
```

## Notes

- Railway backend confirmed streaming correctly via curl
- Frontend code is correct (SSE parsing, flushSync, etc.)
- Issue is **network buffering between Railway and browser**
- Most likely culprit: Vercel edge network
- Quick win: Test localhost → production backend to confirm Vercel is the issue
