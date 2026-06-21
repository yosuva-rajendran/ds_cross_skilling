import os
from fastapi import FastAPI
from groq import Groq
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[Message]

@app.post("/chat")
def chat(request: ChatRequest):

    def generate():
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages= request.messages,
            max_completion_tokens=1024,
            temperature=0.5,
            stream=True
        )

        for chunk in stream:
            content = chunk.choices[0].delta.content

            if content:
                yield content

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )