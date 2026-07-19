"use client";

import { useState, useEffect } from "react";
import {
  listCollections,
  createCollection,
  deleteCollection,
} from "../lib/api";

interface Props {
  collections: string[];
  onRefresh: () => void;
}

export default function CollectionPanel({ collections, onRefresh }: Props) {
  const [newName, setNewName] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setLoading(true);
    setMessage("");
    try {
      await createCollection(newName.trim());
      setMessage(`Collection "${newName}" created`);
      setNewName("");
      onRefresh();
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (name: string) => {
    setLoading(true);
    try {
      await deleteCollection(name);
      setMessage(`Collection "${name}" deleted`);
      onRefresh();
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border rounded-lg p-4 bg-white shadow-sm">
      <h2 className="text-lg font-semibold mb-3">Collections</h2>

      <div className="flex gap-2 mb-3">
        <input
          type="text"
          placeholder="New collection name"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          className="flex-1 border rounded px-3 py-1.5 text-sm"
          onKeyDown={(e) => e.key === "Enter" && handleCreate()}
        />
        <button
          onClick={handleCreate}
          disabled={loading || !newName.trim()}
          className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          Create
        </button>
      </div>

      {collections.length === 0 ? (
        <p className="text-sm text-gray-400">No collections yet.</p>
      ) : (
        <ul className="space-y-1">
          {collections.map((name) => (
            <li key={name} className="flex items-center justify-between text-sm border-b pb-1">
              <span className="font-mono">{name}</span>
              <button
                onClick={() => handleDelete(name)}
                disabled={loading}
                className="text-red-500 hover:text-red-700 text-xs"
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}

      {message && (
        <p className={`text-xs mt-2 ${message.startsWith("Error") ? "text-red-500" : "text-green-600"}`}>
          {message}
        </p>
      )}
    </div>
  );
}
