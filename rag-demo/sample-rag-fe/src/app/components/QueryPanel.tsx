"use client";

import { useState } from "react";
import { queryDocuments, QueryResult } from "../lib/api";

interface Props {
  collections: string[];
}

export default function QueryPanel({ collections }: Props) {
  const [selectedCollection, setSelectedCollection] = useState("");
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [generateAnswer, setGenerateAnswer] = useState(false);
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [results, setResults] = useState<QueryResult[]>([]);
  const [error, setError] = useState("");

  const handleSearch = async () => {
    if (!selectedCollection || !query.trim()) return;
    setLoading(true);
    setAnswer(null);
    setResults([]);
    setError("");
    try {
      const res = await queryDocuments(
        selectedCollection,
        query.trim(),
        topK,
        generateAnswer
      );
      setAnswer(res.answer);
      setResults(res.results);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border rounded-lg p-4 bg-white shadow-sm">
      <h2 className="text-lg font-semibold mb-3">Query</h2>

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

      <label className="block text-sm font-medium mb-1">Question</label>
      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask a question about your documents..."
        rows={3}
        className="w-full border rounded px-3 py-1.5 text-sm mb-3 resize-none"
      />

      <div className="flex items-center gap-4 mb-3">
        <label className="flex items-center gap-1 text-sm">
          Top-K:
          <input
            type="number"
            min={1}
            max={20}
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            className="w-16 border rounded px-2 py-1 text-sm"
          />
        </label>
        <label className="flex items-center gap-1 text-sm">
          <input
            type="checkbox"
            checked={generateAnswer}
            onChange={(e) => setGenerateAnswer(e.target.checked)}
          />
          Generate Answer (LLM)
        </label>
      </div>

      <button
        onClick={handleSearch}
        disabled={loading || !selectedCollection || !query.trim()}
        className="w-full bg-purple-600 text-white py-2 rounded text-sm hover:bg-purple-700 disabled:opacity-50"
      >
        {loading ? "Searching..." : "Search"}
      </button>

      {error && <p className="text-xs text-red-500 mt-2">{error}</p>}

      {answer && (
        <div className="mt-4 p-3 bg-gray-50 border rounded text-sm">
          <p className="font-medium text-xs text-gray-500 mb-1">LLM Answer</p>
          <p className="whitespace-pre-wrap">{answer}</p>
        </div>
      )}

      {results.length > 0 && (
        <div className="mt-4 space-y-2">
          <p className="text-xs font-medium text-gray-500">
            Retrieved Chunks ({results.length})
          </p>
          {results.map((r, i) => (
            <div key={i} className="border rounded p-2 text-xs">
              <div className="flex justify-between mb-1">
                <span className="font-mono text-gray-500">
                  {r.filename} [chunk {r.chunk_index}]
                </span>
                <span className="font-semibold text-blue-600">
                  {r.score.toFixed(4)}
                </span>
              </div>
              <p className="whitespace-pre-wrap">{r.text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
