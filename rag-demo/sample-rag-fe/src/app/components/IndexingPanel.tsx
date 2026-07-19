"use client";

import { useState, useRef } from "react";
import { uploadDocument } from "../lib/api";

interface Props {
  collections: string[];
}

export default function IndexingPanel({ collections }: Props) {
  const [selectedCollection, setSelectedCollection] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async () => {
    if (!selectedCollection || !file) return;
    setLoading(true);
    setResult("");
    setError("");
    try {
      const res = await uploadDocument(selectedCollection, file);
      setResult(
        `Indexed "${res.data.filename}" → ${res.data.chunk_count} chunks (id: ${res.data.document_id})`
      );
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border rounded-lg p-4 bg-white shadow-sm">
      <h2 className="text-lg font-semibold mb-3">Index Document</h2>

      <label className="block text-sm font-medium mb-1">Collection</label>
      <select
        value={selectedCollection}
        onChange={(e) => setSelectedCollection(e.target.value)}
        className="w-full border rounded px-3 py-1.5 text-sm mb-3"
      >
        <option value="">-- select collection --</option>
        {collections.map((name) => (
          <option key={name} value={name}>
            {name}
          </option>
        ))}
      </select>

      <label className="block text-sm font-medium mb-1">PDF File</label>
      <input
        ref={fileInputRef}
        type="file"
        accept="application/pdf"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
        className="w-full border rounded px-3 py-1.5 text-sm mb-3"
      />

      <button
        onClick={handleUpload}
        disabled={loading || !selectedCollection || !file}
        className="w-full bg-green-600 text-white py-2 rounded text-sm hover:bg-green-700 disabled:opacity-50"
      >
        {loading ? "Indexing..." : "Upload & Index"}
      </button>

      {result && <p className="text-xs text-green-600 mt-2">{result}</p>}
      {error && <p className="text-xs text-red-500 mt-2">{error}</p>}
    </div>
  );
}
