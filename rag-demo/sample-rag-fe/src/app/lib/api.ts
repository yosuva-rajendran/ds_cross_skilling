const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Collection {
  name: string;
  status: string;
}

export interface CollectionListResponse {
  collections: string[];
}

export interface UploadResult {
  document_id: string;
  filename: string;
  chunk_count: number;
}

export interface QueryResult {
  text: string;
  score: number;
  filename: string;
  chunk_index: number;
  document_id: string;
}

export interface QueryResponse {
  query: string;
  results: QueryResult[];
  answer: string | null;
}

export async function listCollections(): Promise<string[]> {
  const res = await fetch(`${API_URL}/collections/`);
  if (!res.ok) throw new Error("Failed to list collections");
  const data: CollectionListResponse = await res.json();
  return data.collections;
}

export async function createCollection(
  name: string,
  vectorSize: number = 1536
): Promise<Collection> {
  const res = await fetch(`${API_URL}/collections/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, vector_size: vectorSize }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to create collection");
  }
  return res.json();
}

export async function deleteCollection(name: string): Promise<Collection> {
  const res = await fetch(`${API_URL}/collections/${name}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete collection");
  return res.json();
}

export async function uploadDocument(
  collectionName: string,
  file: File
): Promise<{ message: string; data: UploadResult }> {
  const formData = new FormData();
  formData.append("collection_name", collectionName);
  formData.append("file", file);

  const res = await fetch(`${API_URL}/documents/`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to upload document");
  }
  return res.json();
}

export async function queryDocuments(
  collectionName: string,
  query: string,
  topK: number = 5,
  generateAnswer: boolean = false
): Promise<QueryResponse> {
  const res = await fetch(`${API_URL}/query/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      collection_name: collectionName,
      query,
      top_k: topK,
      generate_answer: generateAnswer,
    }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to query documents");
  }
  return res.json();
}
