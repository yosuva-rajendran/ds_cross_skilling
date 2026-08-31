# Module 12: Building Production APIs

## Sync vs Async vs Streaming

**Sync** — client waits, server processes, returns full response. Simple but slow for LLM calls.

**Async** — server handles many requests concurrently using `async/await`. Essential for I/O-bound LLM calls so one slow response doesn't block others.

**Streaming** — server sends tokens as they're generated. User sees output appearing in real-time instead of waiting 10+ seconds for full response. Uses Server-Sent Events (SSE).

| Pattern | Use When |
|---------|----------|
| Sync | Internal tools, batch processing |
| Async | Multi-user APIs, concurrent requests |
| Streaming | Chat UIs, real-time user-facing apps |

## FastAPI for GenAI

Why FastAPI:
- Native `async` support
- Auto-generated docs (Swagger)
- Pydantic validation built-in
- `StreamingResponse` for SSE
- Easy middleware for auth, rate limiting, CORS

### Project Structure
```
app/
  main.py          # routes and app setup
  models.py        # Pydantic request/response schemas
  llm_service.py   # LLM client wrapper
  middleware.py     # auth, rate limit, error handling
```

### Key Patterns

**Pydantic models** for request validation:
```python
class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    stream: bool = False
```

**StreamingResponse** for SSE:
```python
async def generate():
    async for chunk in llm.stream(prompt):
        yield f"data: {chunk}\n\n"
return StreamingResponse(generate(), media_type="text/event-stream")
```

**BackgroundTasks** for fire-and-forget work:
```python
@app.post("/chat")
async def chat(req: ChatRequest, bg: BackgroundTasks):
    response = await llm.call(req.message)
    bg.add_task(log_to_db, req, response)
    return response
```

## Session Management

- Every conversation gets a UUID
- Store conversation history server-side (Redis or dict for demo)
- Client sends `conversation_id` with each request
- Server loads history, appends new turn, saves back
- Stateless API design — no server affinity needed

## File Handling

- Accept uploads via `UploadFile`
- Validate file type and size before processing
- Process async (don't block the request)
- Clean up temp files after processing

## Error Handling for LLM APIs

LLM calls fail often. Handle:
- **Rate limits** (429) — retry with backoff
- **Context exceeded** (400) — truncate and retry
- **Timeout** — set reasonable limits (30-60s)
- **Content policy** — return safe fallback
- **Server error** (500/503) — retry with backoff
