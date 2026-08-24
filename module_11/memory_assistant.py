import os
import json
import sqlite3
import hashlib
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DB_PATH = "memory_store.db"


# --- Memory Store (SQLite-backed) ---

class MemoryStore:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self._setup()

    def _setup(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                memory_type TEXT,
                content TEXT,
                created_at TEXT,
                access_count INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TEXT
            );
            CREATE TABLE IF NOT EXISTS user_profile (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                preferences TEXT,
                summary TEXT,
                updated_at TEXT
            );
        """)
        self.conn.commit()

    def add_memory(self, user_id, content, memory_type="fact"):
        mem_id = hashlib.md5(f"{user_id}:{content}".encode()).hexdigest()[:12]
        self.conn.execute(
            "INSERT OR REPLACE INTO memories (id, user_id, memory_type, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (mem_id, user_id, memory_type, content, datetime.now().isoformat())
        )
        self.conn.commit()
        return mem_id

    def search_memories(self, user_id, query, limit=5):
        """Simple keyword-based search. In production, use vector similarity."""
        words = query.lower().split()
        rows = self.conn.execute(
            "SELECT content, memory_type, created_at FROM memories WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()

        scored = []
        for content, mtype, created in rows:
            score = sum(1 for w in words if w in content.lower())
            if score > 0:
                scored.append((score, content, mtype, created))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [(c, t, d) for _, c, t, d in scored[:limit]]

    def get_all_memories(self, user_id):
        return self.conn.execute(
            "SELECT content, memory_type, created_at FROM memories WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()

    def save_message(self, user_id, role, content):
        self.conn.execute(
            "INSERT INTO conversations (user_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, role, content, datetime.now().isoformat())
        )
        self.conn.commit()

    def get_recent_messages(self, user_id, limit=10):
        rows = self.conn.execute(
            "SELECT role, content FROM conversations WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
        return list(reversed(rows))

    def update_profile(self, user_id, name=None, preferences=None, summary=None):
        existing = self.conn.execute(
            "SELECT name, preferences, summary FROM user_profile WHERE user_id = ?", (user_id,)
        ).fetchone()

        if existing:
            name = name or existing[0]
            preferences = preferences or existing[1]
            summary = summary or existing[2]
            self.conn.execute(
                "UPDATE user_profile SET name=?, preferences=?, summary=?, updated_at=? WHERE user_id=?",
                (name, preferences, summary, datetime.now().isoformat(), user_id)
            )
        else:
            self.conn.execute(
                "INSERT INTO user_profile (user_id, name, preferences, summary, updated_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, name or "", preferences or "", summary or "", datetime.now().isoformat())
            )
        self.conn.commit()

    def get_profile(self, user_id):
        row = self.conn.execute(
            "SELECT name, preferences, summary FROM user_profile WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row:
            return {"name": row[0], "preferences": row[1], "summary": row[2]}
        return None


# --- Memory Extraction ---

def extract_memories(llm_client, user_message, assistant_response):
    """Ask LLM to extract memorable facts from the conversation turn."""
    prompt = (
        "Extract any personal facts, preferences, or important information from this exchange.\n"
        "Return a JSON list of strings. Each string is one fact.\n"
        "If nothing worth remembering, return [].\n\n"
        f"User: {user_message}\n"
        f"Assistant: {assistant_response}\n\n"
        "Facts (JSON list):"
    )
    try:
        resp = llm_client.chat.completions.create(
            model="nvidia/nemotron-3-super-120b-a12b:free",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        text = resp.choices[0].message.content.strip()
        # try to parse JSON from response
        if "[" in text:
            text = text[text.index("["):text.rindex("]")+1]
            return json.loads(text)
    except Exception:
        pass
    return []


# --- Assistant with Memory ---

class MemoryAssistant:
    def __init__(self, user_id="default"):
        self.user_id = user_id
        self.store = MemoryStore()
        self.client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )

    def _build_context(self, user_message):
        """Assemble context from all memory sources."""
        parts = []

        # user profile
        profile = self.store.get_profile(self.user_id)
        if profile and any(profile.values()):
            parts.append(f"User profile: {profile['name']}. {profile['preferences']}. {profile['summary']}")

        # relevant memories
        memories = self.store.search_memories(self.user_id, user_message, limit=3)
        if memories:
            mem_text = "\n".join(f"- {content} ({mtype})" for content, mtype, _ in memories)
            parts.append(f"Relevant memories:\n{mem_text}")

        return "\n\n".join(parts)

    def chat(self, user_message):
        # save user message
        self.store.save_message(self.user_id, "user", user_message)

        # build system prompt with memory context
        context = self._build_context(user_message)
        system = "You are a helpful personal assistant with memory. You remember past conversations and user preferences."
        if context:
            system += f"\n\nWhat you know about this user:\n{context}"

        # get recent conversation for short-term memory
        recent = self.store.get_recent_messages(self.user_id, limit=8)
        messages = [{"role": "system", "content": system}]
        for role, content in recent:
            messages.append({"role": role, "content": content})

        # call LLM
        try:
            resp = self.client.chat.completions.create(
                model="nvidia/nemotron-3-super-120b-a12b:free",
                messages=messages,
            )
            answer = resp.choices[0].message.content
        except Exception as e:
            answer = f"Sorry, I hit an error: {e}"

        # save assistant response
        self.store.save_message(self.user_id, "assistant", answer)

        # extract and store new memories in background
        new_facts = extract_memories(self.client, user_message, answer)
        for fact in new_facts:
            self.store.add_memory(self.user_id, fact)
            print(f"  [memory saved] {fact}")

        return answer

    def teach(self, fact):
        """Manually add a memory."""
        self.store.add_memory(self.user_id, fact, memory_type="taught")
        print(f"  [remembered] {fact}")

    def recall(self, query):
        """Search memories."""
        results = self.store.search_memories(self.user_id, query)
        return results

    def show_all_memories(self):
        return self.store.get_all_memories(self.user_id)


if __name__ == "__main__":
    assistant = MemoryAssistant(user_id="yosuva")

    # teach it some facts first
    print("Teaching the assistant...\n")
    assistant.teach("Yosuva is a data scientist")
    assistant.teach("Prefers Python and FastAPI")
    assistant.teach("Works at a startup in Chennai")
    assistant.teach("Learning about AI agents and CrewAI")
    assistant.teach("Uses OpenRouter for LLM access")
    assistant.store.update_profile("yosuva", name="Yosuva", preferences="Python, dark mode, concise answers")

    # have a conversation
    print("\n--- Conversation ---\n")

    queries = [
        "Hey, what do you remember about me?",
        "I'm thinking of learning Rust next. What do you think given my background?",
        "What frameworks have I been working with?",
    ]

    for q in queries:
        print(f"You: {q}")
        response = assistant.chat(q)
        print(f"Assistant: {response}\n")

    # show what's stored
    print("\n--- All Stored Memories ---")
    for content, mtype, created in assistant.show_all_memories():
        print(f"  [{mtype}] {content}")
