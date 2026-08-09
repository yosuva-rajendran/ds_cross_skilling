# Retrieval-Augmented Generation (RAG)

Retrieval-Augmented Generation (RAG) is a technique that combines information retrieval
with a generative large language model. Instead of relying only on the model's parametric
knowledge, the system first retrieves relevant chunks from an external knowledge base and
then conditions the generation step on that retrieved context.

## Why RAG

- **Up-to-date information**: The knowledge base can be refreshed without retraining the model.
- **Reduced hallucination**: The model grounds its answer in retrieved evidence.
- **Source attribution**: Answers can cite the documents they were generated from.
- **Domain adaptation**: Organisations can answer questions about their private documents.

## RAG pipeline stages

1. **Ingestion**: Documents are loaded, split into chunks, embedded, and indexed in a
   vector store.
2. **Retrieval**: At query time the question is embedded and the most similar chunks are
   retrieved using vector similarity (e.g. cosine similarity).
3. **Generation**: The retrieved chunks are inserted into a prompt as context and the LLM
   generates a grounded answer.

## Advanced RAG techniques

- **Query rewriting**: Transform the user's question into a better retrieval query.
- **Retrieval grading**: Score retrieved chunks for relevance and filter out irrelevant ones.
- **Hybrid search**: Combine dense vector search with keyword (BM25) search.
- **Re-ranking**: Use a cross-encoder to re-rank the top-k candidates after retrieval.
- **Self-reflection / corrective RAG**: Let the LLM judge whether the retrieved context is
  good enough, and re-retrieve or rewrite the query if not.

## Vector stores

ChromaDB is an open-source, embedded vector database commonly used for RAG. It persists
collections to local disk, supports metadata filtering, and stores the embedding vectors
alongside the original text so nothing else needs to be persisted.
