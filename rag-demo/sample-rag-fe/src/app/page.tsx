"use client";

import { useState, useEffect, useCallback } from "react";
import { listCollections } from "./lib/api";
import CollectionPanel from "./components/CollectionPanel";
import IndexingPanel from "./components/IndexingPanel";
import QueryPanel from "./components/QueryPanel";

export default function Home() {
  const [collections, setCollections] = useState<string[]>([]);

  const fetchCollections = useCallback(async () => {
    try {
      const names = await listCollections();
      setCollections(names);
    } catch {
      setCollections([]);
    }
  }, []);

  useEffect(() => {
    fetchCollections();
  }, [fetchCollections]);

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white border-b px-6 py-4">
        <h1 className="text-xl font-bold">RAG Demo</h1>
        <p className="text-sm text-gray-500">
          Upload PDFs, index them, and query with semantic search
        </p>
      </header>

      <main className="max-w-7xl mx-auto p-6">
        <div className="mb-6">
          <CollectionPanel
            collections={collections}
            onRefresh={fetchCollections}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <IndexingPanel collections={collections} />
          <QueryPanel collections={collections} />
        </div>
      </main>
    </div>
  );
}
