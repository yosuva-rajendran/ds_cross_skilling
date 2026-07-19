import cohere
from groq import Groq
from google import genai
from google.genai import types

from app.config import settings
from app.repositories.document_repository import DocumentRepository
from app.schemas.query import QueryResponse, QueryResult


class RetrievalService:

    def __init__(self):
        self.repository = DocumentRepository()
        self.genai_client = genai.Client(api_key=settings.google_api_key)
        self.groq_client = Groq(api_key=settings.groq_api_key)
        self.cohere_client = cohere.ClientV2(api_key=settings.cohere_api_key)

    def query(
        self,
        collection_name: str,
        query: str,
        top_k: int = 5,
        generate_answer: bool = False,
    ) -> QueryResponse:

        # Step 1: Embed the query
        response = self.genai_client.models.embed_content(
            model="gemini-embedding-001",
            contents=query,
            config=types.EmbedContentConfig(output_dimensionality=1536),
        )
        query_vector = response.embeddings[0].values

        # Step 2: Search Qdrant (fetch more candidates for reranking)
        candidates = self.repository.search(
            collection_name=collection_name,
            query_vector=query_vector,
            top_k=top_k * 4,
        )

        # Step 3: Rerank with Cohere
        results = self._rerank(query, candidates, top_k)

        # Step 4: Optionally generate answer via Groq LLM
        answer = None
        if generate_answer:
            answer = self._generate_answer(query, results)

        return QueryResponse(
            query=query,
            results=[QueryResult(**r) for r in results],
            answer=answer,
        )

    def _rerank(self, query: str, candidates: list[dict], top_k: int) -> list[dict]:
        documents = [c["text"] for c in candidates]

        response = self.cohere_client.rerank(
            model="rerank-v3.5",
            query=query,
            documents=documents,
            top_n=top_k,
        )

        reranked = []
        for result in response.results:
            candidate = candidates[result.index]
            reranked.append({
                "text": candidate["text"],
                "score": result.relevance_score,
                "filename": candidate["filename"],
                "chunk_index": candidate["chunk_index"],
                "document_id": candidate["document_id"],
            })

        return reranked

    def _generate_answer(self, query: str, results: list[dict]) -> str:
        context = "\n\n---\n\n".join(
            f"[Source: {r['filename']}, chunk {r['chunk_index']}]\n{r['text']}"
            for r in results
        )

        prompt = (
            "You are a helpful assistant. Answer the user's question based on "
            "the following context extracted from documents. If the context does "
            "not contain enough information, say so.\n\n"
            f"## Context\n\n{context}\n\n"
            f"## Question\n\n{query}\n\n"
            "## Answer\n"
        )

        chat = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
        )

        return chat.choices[0].message.content
