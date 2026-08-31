import os
import uuid
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI

load_dotenv()

app = FastAPI(title="GenAI Chat API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

client = AsyncOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)
MODEL = "nvidia/nemotron-3-super-120b-a12b:free"

# in-memory session store (use Redis in production)
sessions: dict[str, list[dict]] = {}


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    stream: bool = False


class ChatResponse(BaseModel):
    conversation_id: str
    response: str


def get_or_create_session(conv_id: str | None) -> tuple[str, list[dict]]:
    if conv_id and conv_id in sessions:
        return conv_id, sessions[conv_id]
    new_id = str(uuid.uuid4())[:8]
    sessions[new_id] = [{"role": "system", "content": "You are a helpful assistant. Keep answers short."}]
    return new_id, sessions[new_id]


def log_request(conv_id, user_msg, assistant_msg):
    """Simulate logging to DB — runs as background task."""
    print(f"  [log] conv={conv_id} | user={user_msg[:40]}... | response={assistant_msg[:40]}...")


# --- Endpoint 1: Regular async chat ---

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, bg: BackgroundTasks):
    conv_id, history = get_or_create_session(req.conversation_id)
    history.append({"role": "user", "content": req.message})

    resp = await client.chat.completions.create(model=MODEL, messages=history)
    answer = resp.choices[0].message.content if resp.choices else "(empty response)"
    answer = answer or "(empty response)"

    history.append({"role": "assistant", "content": answer})
    bg.add_task(log_request, conv_id, req.message, answer)

    return ChatResponse(conversation_id=conv_id, response=answer)


# --- Endpoint 2: Streaming chat (SSE) ---

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    conv_id, history = get_or_create_session(req.conversation_id)
    history.append({"role": "user", "content": req.message})

    async def generate():
        full_response = ""
        stream = await client.chat.completions.create(model=MODEL, messages=history, stream=True)
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full_response += delta
                yield f"data: {delta}\n\n"
        history.append({"role": "assistant", "content": full_response})
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"X-Conversation-ID": conv_id})


# --- Endpoint 3: List sessions ---

@app.get("/sessions")
async def list_sessions():
    return {cid: len(msgs) for cid, msgs in sessions.items()}


# --- Endpoint 4: Health check ---

@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL}


if __name__ == "__main__":
    import uvicorn
    print("Starting GenAI API...")
    print("Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
