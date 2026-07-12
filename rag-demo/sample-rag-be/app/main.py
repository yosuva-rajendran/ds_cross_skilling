from fastapi import FastAPI
from app.api.collections import router as collections_router
from app.api.document import router as documents_router

app = FastAPI(title="RAG API")

app.include_router(collections_router)
app.include_router(documents_router)