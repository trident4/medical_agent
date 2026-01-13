# Chat API Frontend Integration Guide

This guide explains how to integrate the Doctor's Assistant Chat API into your frontend application.

---

## Prerequisites

1. User must be authenticated with `ADMIN` or `DOCTOR` role
2. You need a valid JWT token from `/api/v1/auth/login`

---

## Endpoints

| Endpoint              | Method | Description                |
| --------------------- | ------ | -------------------------- |
| `/api/v1/chat/`       | POST   | Non-streaming chat request |
| `/api/v1/chat/stream` | POST   | SSE streaming chat request |

---

## Authentication

All chat endpoints require a Bearer token in the Authorization header:

```javascript
const headers = {
  Authorization: `Bearer ${token}`,
  "Content-Type": "application/json",
};
```

---

## Non-Streaming Chat

### Request

```javascript
const response = await fetch("/api/v1/chat/", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    message: "Show visits for Michael Brown",
    session_id: "user-123-session", // Use consistent session_id for conversation context
  }),
});

const data = await response.json();
console.log(data);
// { response: "Found 3 visits...", intent: "search", results_count: 3 }
```

### Response Schema

```typescript
interface ChatResponse {
  response: string; // The AI-generated response
  intent: string; // Detected intent: search, detail, summarize, analytics, chitchat
  results_count: number; // Number of database results found
}
```

### React Example

```jsx
import { useState } from "react";

function ChatComponent({ token }) {
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => `session-${Date.now()}`);

  const sendMessage = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/chat/", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          session_id: sessionId,
        }),
      });

      if (!res.ok) throw new Error("Chat failed");

      const data = await res.json();
      setResponse(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Ask about patients..."
      />
      <button onClick={sendMessage} disabled={loading}>
        {loading ? "Thinking..." : "Send"}
      </button>

      {response && (
        <div>
          <p>
            <strong>Intent:</strong> {response.intent}
          </p>
          <p>
            <strong>Results:</strong> {response.results_count}
          </p>
          <p>{response.response}</p>
        </div>
      )}
    </div>
  );
}
```

---

## Streaming Chat (SSE)

For real-time streaming responses, use Server-Sent Events (SSE).

### JavaScript (Vanilla)

```javascript
async function streamChat(message, sessionId, token, onChunk, onDone) {
  const response = await fetch("/api/v1/chat/stream", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const text = decoder.decode(value);
    const lines = text.split("\n\n");

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const json = JSON.parse(line.slice(6));

        if (json.type === "done") {
          onDone();
          return;
        }

        if (json.type === "error") {
          console.error("Stream error:", json.error);
          return;
        }

        // Node update with partial data
        onChunk(json.node, json.data);
      }
    }
  }
}

// Usage
streamChat(
  "What are the statistics for diabetes patients?",
  "session-123",
  userToken,
  (node, data) => {
    console.log(`Node ${node} completed:`, data);
  },
  () => {
    console.log("Stream finished");
  }
);
```

### SSE Event Format

Each event contains:

```json
{
  "node": "extract_intent", // Node that just completed
  "data": {
    // Output from that node
    "intent": "analytics",
    "filters": {}
  }
}
```

Final event:

```json
{ "type": "done" }
```

Error event:

```json
{ "type": "error", "error": "Error message" }
```

### React Streaming Example

```jsx
import { useState, useCallback } from "react";

function StreamingChat({ token }) {
  const [message, setMessage] = useState("");
  const [chunks, setChunks] = useState([]);
  const [streaming, setStreaming] = useState(false);
  const [sessionId] = useState(() => `session-${Date.now()}`);

  const streamMessage = useCallback(async () => {
    setStreaming(true);
    setChunks([]);

    const response = await fetch("/api/v1/chat/stream", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message, session_id: sessionId }),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = decoder.decode(value);
      for (const line of text.split("\n\n")) {
        if (line.startsWith("data: ")) {
          const json = JSON.parse(line.slice(6));

          if (json.type === "done") {
            setStreaming(false);
            return;
          }

          setChunks((prev) => [...prev, json]);
        }
      }
    }

    setStreaming(false);
  }, [message, sessionId, token]);

  return (
    <div>
      <input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Ask about patients..."
      />
      <button onClick={streamMessage} disabled={streaming}>
        {streaming ? "Processing..." : "Stream"}
      </button>

      <div>
        {chunks.map((chunk, i) => (
          <div key={i} style={{ padding: "8px", borderLeft: "3px solid #ccc" }}>
            <strong>{chunk.node}</strong>
            <pre>{JSON.stringify(chunk.data, null, 2)}</pre>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## Session Management

The `session_id` parameter enables conversation context:

```javascript
// Same session_id = conversation continues
const sessionId = "user-123-session";

// Message 1
await chat("Show visits for Michael Brown", sessionId);
// Response: "Found 3 visits for Michael Brown..."

// Message 2 (same session)
await chat("What was his last diagnosis?", sessionId);
// Response: "Michael Brown's last diagnosis was..." (remembers context)

// New session = fresh start
await chat("What was his last diagnosis?", "new-session");
// Response: "I need more context. Which patient..."
```

---

## Error Handling

| Status | Meaning                                  |
| ------ | ---------------------------------------- |
| 401    | Not authenticated                        |
| 403    | Insufficient role (need ADMIN or DOCTOR) |
| 422    | Invalid request body                     |
| 500    | Server error                             |

```javascript
try {
  const response = await fetch('/api/v1/chat/', { ... });

  if (response.status === 401) {
    // Redirect to login
    window.location.href = '/login';
    return;
  }

  if (response.status === 403) {
    alert('You do not have permission to use the chat feature');
    return;
  }

  if (!response.ok) {
    const error = await response.json();
    console.error('Chat error:', error.detail);
    return;
  }

  const data = await response.json();
  // Handle success
} catch (err) {
  console.error('Network error:', err);
}
```

---

## Example Queries

| Query                              | Expected Intent                 |
| ---------------------------------- | ------------------------------- |
| "Hello, how are you?"              | chitchat                        |
| "Show all patients"                | search                          |
| "Details for patient ID 5"         | detail                          |
| "Summarize last 10 visits"         | summarize                       |
| "How many patients have diabetes?" | analytics                       |
| "Show visits for Michael Brown"    | search (with entity resolution) |
