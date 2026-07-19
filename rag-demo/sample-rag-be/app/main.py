from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.collections import router as collections_router
from app.api.document import router as documents_router
from app.api.query import router as query_router

app = FastAPI(title="RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(collections_router)
app.include_router(documents_router)
app.include_router(query_router)