
import uuid
import fitz

from fastapi import UploadFile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google import genai
from google.genai import types

from app.config import settings
from app.repositories.document_repository import DocumentRepository


class IndexingService:

    def __init__(self):
        self.repository = DocumentRepository()

        self.embedding_client = genai.Client(
            api_key=settings.google_api_key
        )

    async def index_document(
        self,
        collection_name: str,
        file: UploadFile,
    ):

        # Step 1 : Read PDF
        pdf_bytes = await file.read()
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""

        for page in document:
            text += page.get_text()

        document.close()

        if not text.strip():
            raise Exception("PDF contains no text.")

        # Step 2 : Chunking

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )

        chunks = splitter.split_text(text)
        # Step 3 : Embeddings

        response = self.embedding_client.models.embed_content(
            model="gemini-embedding-001",
            contents=chunks,
            config=types.EmbedContentConfig(
                output_dimensionality=1536
            )
        )

        vectors = [
            embedding.values
            for embedding in response.embeddings
        ]

        # Step 4 : Store

        document_id = str(uuid.uuid4())

        self.repository.store(
            collection_name=collection_name,
            document_id=document_id,
            filename=file.filename,
            chunks=chunks,
            vectors=vectors,
        )

        return {
            "document_id": document_id,
            "filename": file.filename,
            "chunk_count": len(chunks),
        }