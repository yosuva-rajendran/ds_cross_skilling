import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)
MODEL = "nvidia/nemotron-3-super-120b-a12b:free"


def count_tokens_approx(messages):
    """Rough token count: ~4 chars per token."""
    total_chars = sum(len(m["content"]) for m in messages if m.get("content"))
    return total_chars // 4


# Strategy 1: Full history
class FullHistory:
    def __init__(self):
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]

    def add(self, role, content):
        self.messages.append({"role": role, "content": content})

    def get_messages(self):
        return self.messages.copy()

    def stats(self):
        return f"msgs={len(self.messages)}, ~tokens={count_tokens_approx(self.messages)}"


# Strategy 2: Buffer window
class BufferWindow:
    def __init__(self, window_size=6):
        self.all_messages = []
        self.system = {"role": "system", "content": "You are a helpful assistant."}
        self.window_size = window_size

    def add(self, role, content):
        self.all_messages.append({"role": role, "content": content})

    def get_messages(self):
        recent = self.all_messages[-self.window_size:]
        return [self.system] + recent

    def stats(self):
        msgs = self.get_messages()
        return f"msgs={len(msgs)}, ~tokens={count_tokens_approx(msgs)} (total stored: {len(self.all_messages)})"


# Strategy 3: Summary buffer
class SummaryBuffer:
    def __init__(self, recent_limit=4):
        self.all_messages = []
        self.summary = ""
        self.recent_limit = recent_limit

    def add(self, role, content):
        self.all_messages.append({"role": role, "content": content})
        if len(self.all_messages) > self.recent_limit * 2:
            self._summarize_old()

    def _summarize_old(self):
        old = self.all_messages[:-self.recent_limit]
        old_text = "\n".join(f"{m['role']}: {m['content']}" for m in old)

        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": f"Summarize this conversation in 2-3 sentences:\n{old_text}"}],
            )
            self.summary = resp.choices[0].message.content
        except Exception:
            self.summary = f"(Earlier: {len(old)} messages about various topics)"

        self.all_messages = self.all_messages[-self.recent_limit:]

    def get_messages(self):
        system_content = "You are a helpful assistant."
        if self.summary:
            system_content += f"\n\nSummary of earlier conversation:\n{self.summary}"
        messages = [{"role": "system", "content": system_content}]
        messages.extend(self.all_messages)
        return messages

    def stats(self):
        msgs = self.get_messages()
        has_summary = "yes" if self.summary else "no"
        return f"msgs={len(msgs)}, ~tokens={count_tokens_approx(msgs)}, summary={has_summary}"


# Strategy 4: Token-aware truncation
class TokenAware:
    def __init__(self, max_tokens=500):
        self.all_messages = []
        self.system = {"role": "system", "content": "You are a helpful assistant."}
        self.max_tokens = max_tokens

    def add(self, role, content):
        self.all_messages.append({"role": role, "content": content})

    def get_messages(self):
        messages = [self.system] + self.all_messages.copy()
        while count_tokens_approx(messages) > self.max_tokens and len(messages) > 2:
            messages.pop(1)
        return messages

    def stats(self):
        msgs = self.get_messages()
        return f"msgs={len(msgs)}, ~tokens={count_tokens_approx(msgs)} (budget: {self.max_tokens})"


if __name__ == "__main__":
    # simulate a conversation
    conversation = [
        ("user", "My name is Yosuva and I'm a data scientist."),
        ("assistant", "Nice to meet you, Yosuva! How can I help you today?"),
        ("user", "I work with Python, pandas, and scikit-learn mostly."),
        ("assistant", "Great stack! Those are fundamental tools for data science."),
        ("user", "I'm now learning about AI agents and LLMs."),
        ("assistant", "Exciting area! Agents combine LLMs with tools and memory for autonomous tasks."),
        ("user", "I've been using CrewAI and LangGraph."),
        ("assistant", "Both excellent choices. CrewAI for quick prototyping, LangGraph for production control."),
        ("user", "What was my name again?"),
        ("assistant", "Your name is Yosuva!"),
        ("user", "What tools do I use for data science?"),
    ]

    strategies = {
        "Full History": FullHistory(),
        "Buffer Window (last 6)": BufferWindow(window_size=6),
        "Summary Buffer": SummaryBuffer(recent_limit=4),
        "Token-Aware (500 tok)": TokenAware(max_tokens=500),
    }

    print("=" * 60)
    print("Short-Term Memory Strategy Comparison")
    print("=" * 60)

    # feed all messages into each strategy
    for role, content in conversation:
        for strat in strategies.values():
            strat.add(role, content)

    print(f"\nAfter {len(conversation)} messages:\n")
    for name, strat in strategies.items():
        msgs = strat.get_messages()
        # check if "Yosuva" is still in context
        all_text = " ".join(m.get("content", "") for m in msgs)
        has_name = "Yosuva" in all_text
        has_tools = "pandas" in all_text or "scikit" in all_text

        print(f"  {name}:")
        print(f"    {strat.stats()}")
        print(f"    Remembers name: {'yes' if has_name else 'NO'}")
        print(f"    Remembers tools: {'yes' if has_tools else 'NO'}")
        print()

    print("-" * 60)
    print("Key insight: Buffer Window loses early context (name, tools).")
    print("Summary Buffer preserves facts in summary while staying compact.")
    print("Token-Aware gives precise budget control.")
