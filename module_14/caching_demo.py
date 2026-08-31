"""
Demonstrates exact-match caching, simple semantic caching,
and model routing by query complexity.
No vector DB needed — uses basic cosine similarity on word counts.
"""

import os
import time
import hashlib
import math
import sys
from collections import Counter
from dotenv import load_dotenv
from openai import OpenAI

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)
MODEL = "nvidia/nemotron-3-super-120b-a12b:free"


# --- Exact-Match Cache ---

class ExactCache:
    def __init__(self):
        self.store = {}
        self.hits = 0
        self.misses = 0

    def _hash(self, text):
        return hashlib.md5(text.strip().lower().encode()).hexdigest()

    def get(self, prompt):
        key = self._hash(prompt)
        if key in self.store:
            self.hits += 1
            return self.store[key]
        self.misses += 1
        return None

    def set(self, prompt, response):
        self.store[self._hash(prompt)] = response

    def stats(self):
        total = self.hits + self.misses
        rate = (self.hits / total * 100) if total else 0
        return f"hits={self.hits}, misses={self.misses}, rate={rate:.0f}%"


# --- Semantic Cache (lightweight, no embeddings API) ---

class SemanticCache:
    """Uses bag-of-words cosine similarity instead of real embeddings.
    In production, use actual embeddings + vector DB."""

    def __init__(self, threshold=0.75):
        self.entries = []  # list of (words_counter, prompt, response)
        self.threshold = threshold
        self.hits = 0
        self.misses = 0

    def _tokenize(self, text):
        words = text.strip().lower().split()
        stopwords = {"a", "an", "the", "is", "are", "was", "were", "what", "how", "do", "does", "in", "of", "to", "for"}
        return Counter(w for w in words if w not in stopwords)

    def _cosine_sim(self, a, b):
        common = set(a.keys()) & set(b.keys())
        dot = sum(a[k] * b[k] for k in common)
        mag_a = math.sqrt(sum(v ** 2 for v in a.values()))
        mag_b = math.sqrt(sum(v ** 2 for v in b.values()))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    def get(self, prompt):
        query_vec = self._tokenize(prompt)
        best_score, best_response = 0, None
        for vec, cached_prompt, response in self.entries:
            score = self._cosine_sim(query_vec, vec)
            if score > best_score:
                best_score, best_response = score, response

        if best_score >= self.threshold:
            self.hits += 1
            return best_response, best_score
        self.misses += 1
        return None, best_score

    def set(self, prompt, response):
        self.entries.append((self._tokenize(prompt), prompt, response))

    def stats(self):
        total = self.hits + self.misses
        rate = (self.hits / total * 100) if total else 0
        return f"hits={self.hits}, misses={self.misses}, rate={rate:.0f}%"


# --- Model Router ---

def classify_complexity(query):
    """Simple rule-based complexity classifier."""
    simple_keywords = {"hi", "hello", "hey", "thanks", "bye", "what is", "define", "who is"}
    complex_keywords = {"compare", "analyze", "explain why", "step by step", "implement", "design", "debug", "optimize"}

    q = query.lower()
    for kw in complex_keywords:
        if kw in q:
            return "complex"
    for kw in simple_keywords:
        if kw in q:
            return "simple"

    word_count = len(q.split())
    if word_count > 30:
        return "complex"
    if word_count < 8:
        return "simple"
    return "medium"


def route_model(query):
    """Pick model based on query complexity."""
    level = classify_complexity(query)
    routing = {
        "simple": ("nvidia/nemotron-3-nano-30b-a3b:free", "nano"),
        "medium": (MODEL, "standard"),
        "complex": (MODEL, "standard"),  # would use gpt-4o in production
    }
    model, label = routing[level]
    return model, level, label


def call_llm(prompt):
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    content = resp.choices[0].message.content if resp.choices else None
    return content or "(empty response)"


if __name__ == "__main__":
    exact = ExactCache()
    semantic = SemanticCache(threshold=0.6)

    queries = [
        "What is Python?",
        "What is Python?",                    # exact duplicate
        "Explain Python programming",         # semantically similar
        "What is JavaScript?",                # different topic
        "Explain Python programming language", # similar again
        "How to cook pasta",                  # unrelated
    ]

    print("=" * 60)
    print("Part 1: Exact-Match Cache")
    print("=" * 60)

    for q in queries:
        cached = exact.get(q)
        if cached:
            print(f"  CACHE HIT: '{q[:40]}' -> {cached[:50]}...")
        else:
            print(f"  CACHE MISS: '{q[:40]}' -> calling LLM...")
            resp = call_llm(q)
            exact.set(q, resp)
            print(f"    Response: {resp[:60]}...")
    print(f"\n  Stats: {exact.stats()}\n")

    print("=" * 60)
    print("Part 2: Semantic Cache")
    print("=" * 60)

    for q in queries:
        cached, score = semantic.get(q)
        if cached:
            print(f"  SEM HIT ({score:.2f}): '{q[:40]}' -> {cached[:50]}...")
        else:
            print(f"  SEM MISS ({score:.2f}): '{q[:40]}' -> calling LLM...")
            resp = call_llm(q)
            semantic.set(q, resp)
            print(f"    Response: {resp[:60]}...")
    print(f"\n  Stats: {semantic.stats()}\n")

    print("=" * 60)
    print("Part 3: Model Routing")
    print("=" * 60)

    routing_queries = [
        "Hi there",
        "What is Python?",
        "Compare Python and Rust for building web APIs, considering performance, ecosystem, and developer experience",
        "Explain step by step how to implement a binary search tree",
        "Thanks!",
    ]

    for q in routing_queries:
        model, level, label = route_model(q)
        print(f"  [{level:7s}] -> {label:10s} | '{q[:60]}'")
