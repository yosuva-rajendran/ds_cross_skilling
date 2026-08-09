# Embeddings and Vector Search

Embeddings are a way to represent text as a list of numbers (a vector) that captures its
meaning. Texts that mean similar things are placed near each other in this numeric space,
so their vectors end up close together.

## How embeddings work

An embedding model, such as Google's gemini-embedding-001, is trained to map words,
sentences, and paragraphs into a high-dimensional vector space. For example, the phrase
"the capital of France" and "Paris" will produce vectors that are close together, while
"baking a cake" produces a vector that is far away. The embedding model used in this
project returns 3072 numbers per piece of text.

## Similarity measures

Once text is represented as vectors, we can measure similarity:

- **Cosine similarity** measures the angle between two vectors, ignoring their length.
  This is the default used by ChromaDB in this project. A cosine score of 1 means the
  vectors point in the same direction (very similar); 0 means unrelated.
- **Euclidean distance** measures the straight-line distance between the tips of the
  vectors.

## Vector search at query time

When you ask the RAG pipeline a question, the same embedding model converts the question
into a vector. ChromaDB then finds the stored document chunks whose vectors are closest to
the question's vector and returns them as candidate context. The number of candidates
returned is controlled by the `k` parameter (RETRIEVE_K, default 4).

## Why the same model matters

The question and the documents must be embedded with the same model, using the same
dimensionality. If you indexed documents with one embedding model and then searched with a
different one, the vectors would live in different spaces and the similarity comparison
would be meaningless. This is why a single `get_embeddings()` function is shared by both
the ingest script and the retrieval step.

## Storing embeddings

ChromaDB stores each chunk's text, its metadata (such as the source filename), and its
embedding vector together in a collection persisted to the local `chroma_db` directory.
Because the vectors are stored alongside the text, no other persistence is needed for the
RAG pipeline to work.
