# Module 11: Memory Systems

## Why Memory Matters

Without memory, every conversation starts from zero. The LLM has no idea who you are,
what you discussed yesterday, or what your preferences are.

Memory gives agents:
- **Continuity** — remembers past interactions
- **Personalization** — knows user preferences
- **Context** — retrieves relevant information at the right time
- **Learning** — improves over time from experience

---

## Types of Memory

### In-Context (Short-Term) Memory
The conversation history itself. Messages list passed to the LLM on every call.
Limited by context window size (4K to 128K+ tokens depending on model).

**Pros:** Simple, always available, no extra infrastructure.
**Cons:** Expensive (tokens), limited size, lost when session ends.

### External (Long-Term) Memory
Stored outside the context window — in databases, vector stores, files.
Retrieved selectively when relevant.

**Pros:** Unlimited storage, persists across sessions, cost-efficient.
**Cons:** Retrieval can miss relevant info, adds latency, needs infrastructure.

### Episodic Memory
Remembers specific events and experiences.
"Last Tuesday, the user asked about deploying to AWS and had issues with IAM roles."

Like a diary — timestamped, sequential, tied to specific interactions.

### Semantic Memory
General knowledge and facts about the world or the user.
"The user prefers Python over JavaScript. They work at a startup. They use PostgreSQL."

Like a knowledge base — structured, factual, not tied to specific moments.

### Procedural Memory
How to do things — learned patterns and workflows.
"When the user says 'deploy', they mean push to staging first, then production after approval."

Like muscle memory — action patterns learned from repetition.

---

## Short-Term Memory Management

### Conversation History as Messages List
Simplest approach. Keep all messages and pass them every time.

```python
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "My name is Yosuva"},
    {"role": "assistant", "content": "Nice to meet you, Yosuva!"},
    {"role": "user", "content": "What's my name?"},
]
# LLM sees everything, can answer "Yosuva"
```

Works fine until you hit token limits.

### Buffer Window — Last N Turns
Keep only the last N messages. Simple sliding window.

```python
window_size = 10
messages = all_messages[-window_size:]
```

**Problem:** Loses early context. If user said their name 20 messages ago, it's gone.

### Summarization of Old Turns
When history gets long, summarize older messages into a condensed version.

```
[System] Summary of earlier conversation:
- User is Yosuva, a data scientist at TechCorp
- Discussed Python best practices
- User prefers FastAPI over Flask
[Recent messages follow normally...]
```

**Tradeoff:** Loses detail but preserves key facts. Costs one extra LLM call to summarize.

### Token-Aware Truncation
Count tokens, not messages. Remove oldest messages until under budget.

```python
max_tokens = 3000
while count_tokens(messages) > max_tokens:
    messages.pop(1)  # keep system prompt, remove oldest user/assistant pair
```

More precise than message count, respects model limits exactly.

### Summary Buffer — Hybrid Approach
Combine summarization with a recent buffer:
- Keep last 5 messages verbatim (recent context)
- Summarize everything before that into a running summary
- Prepend summary as part of system prompt

Best of both worlds. Used by LangChain's `ConversationSummaryBufferMemory`.

---

## Long-Term Memory with Vector Stores

### How It Works
1. Take a piece of information (fact, conversation snippet, preference)
2. Convert it to an embedding vector (using OpenAI, Sentence Transformers, etc.)
3. Store in a vector database
4. At query time, embed the current question
5. Find the most similar stored memories
6. Inject relevant ones into context

### Storing User Facts as Embeddings
```
"User prefers dark mode" → [0.12, -0.34, 0.56, ...]
"User works with Python and FastAPI" → [0.08, -0.22, 0.71, ...]
"User's timezone is IST" → [0.15, -0.41, 0.33, ...]
```

### Storing Past Conversation Summaries
After each session, summarize and store:
```
"2026-08-20: Discussed CrewAI multi-agent setup. User built a tech radar crew."
"2026-08-21: Debugged OpenRouter free model issues. Switched to nemotron."
```

### Retrieving Relevant Memories
When user asks "What framework did we discuss last week?":
1. Embed the query
2. Search vector store for similar memories
3. Return top-K matches
4. Inject into prompt as context

### Memory Consolidation
Over time, merge related memories:
- "User likes Python" + "User uses FastAPI" + "User prefers type hints"
  → "User is a Python developer who prefers FastAPI with strict typing"

Reduces redundancy, improves retrieval.

### Memory Expiry and Freshness
Not all memories stay relevant forever:
- Assign timestamps to memories
- Decay relevance score over time
- Remove or archive stale memories
- Boost recent memories in retrieval ranking

---

## External State Stores

### Redis — Session State
Fast, in-memory key-value store. Great for:
- Current session state
- Short-lived caches
- Real-time data

```python
redis_client.set(f"user:{user_id}:context", json.dumps(state), ex=3600)
```

### PostgreSQL — Structured Memory
Relational database for:
- User profiles
- Conversation logs
- Structured facts with relationships

```sql
CREATE TABLE user_memories (
    id SERIAL PRIMARY KEY,
    user_id TEXT,
    memory_type TEXT,  -- 'preference', 'fact', 'episode'
    content TEXT,
    created_at TIMESTAMP,
    relevance_score FLOAT
);
```

### SQLite — Local Persistence
File-based database, zero setup:
- Local agents
- Development/testing
- Single-user applications

Perfect for learning and prototyping.

### LangGraph Checkpointers
LangGraph has built-in state persistence:
- `MemorySaver` — in-memory (dev only)
- `SqliteSaver` — local file
- `PostgresSaver` — production

Saves full graph state, allows pause/resume of agent workflows.

---

## Memory in Practice

### Injecting Retrieved Memories into System Prompt

```python
relevant_memories = vector_store.search(user_query, top_k=3)

system_prompt = f"""You are a helpful assistant.

Here's what you remember about this user:
{chr(10).join(relevant_memories)}

Use this context to personalize your response.
"""
```

### User Profile Memory Across Sessions
Build a persistent user profile:
- Name, preferences, expertise level
- Past topics discussed
- Common tasks and workflows
- Update after each session

### Project Context Memory
For coding assistants:
- Project structure and tech stack
- Decisions made and why
- Known bugs and workarounds
- Team conventions

### Mem0 — Open-Source Memory Layer
- Automatic memory extraction from conversations
- Vector + graph storage
- User-level and session-level memory
- Simple API: `add()`, `search()`, `get_all()`
- Self-hosted or cloud

```python
from mem0 import Memory
m = Memory()
m.add("I prefer dark mode and use VSCode", user_id="yosuva")
results = m.search("What editor does the user prefer?", user_id="yosuva")
```

### Zep — LLM-Specific Memory Store
- Built specifically for LLM applications
- Auto-summarizes conversations
- Extracts entities and relationships
- Temporal awareness (knows when things happened)
- Handles memory decay and relevance

---

## Choosing the Right Memory Strategy

| Use Case | Strategy |
|----------|----------|
| Simple chatbot | Buffer window (last N messages) |
| Long conversations | Summary buffer |
| Cross-session personalization | Vector store + user profile |
| Agent with tools | LangGraph checkpointer |
| Multi-user production app | Mem0 or Zep + PostgreSQL |
| Local/offline agent | SQLite + sentence-transformers |

---

## Key Takeaways

1. Start with conversation history — it's free and works for short interactions
2. Add summarization when conversations get long (saves tokens)
3. Use vector stores for cross-session memory (user facts, past topics)
4. SQLite is perfect for local development — no setup needed
5. Separate memory types: what the user likes (semantic) vs what happened (episodic)
6. Always inject memories into the system prompt — not the user message
7. Memory retrieval is imperfect — design for graceful handling of missing context
