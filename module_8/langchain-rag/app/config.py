import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/auto")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")

CHROMA_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "langchain_rag"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
RETRIEVE_K = 4

DATA_DIR = BASE_DIR / "data"
