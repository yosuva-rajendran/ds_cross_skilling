"""
Simple observability wrapper for LLM calls.
Tracks latency, tokens, cost, errors — logs everything to SQLite.
No external dependencies beyond openai.
"""

import os
import time
import json
import sqlite3
import uuid
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DB_PATH = "llm_traces.db"

# cost per 1M tokens (approximate for common models)
COST_TABLE = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
    "default": {"input": 0.0, "output": 0.0},  # free models
}


class LLMTracer:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                model TEXT,
                prompt_preview TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                total_tokens INTEGER,
                latency_ms REAL,
                cost_usd REAL,
                status TEXT,
                error TEXT
            )
        """)
        self.conn.commit()
        self.client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )

    def _estimate_cost(self, model, input_tok, output_tok):
        rates = COST_TABLE.get(model, COST_TABLE["default"])
        return (input_tok * rates["input"] + output_tok * rates["output"]) / 1_000_000

    def _log(self, trace_id, model, prompt, usage, latency, status, error=None):
        self.conn.execute(
            "INSERT OR IGNORE INTO traces VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                trace_id,
                datetime.now().isoformat(),
                model,
                prompt[:100],
                usage.get("input", 0),
                usage.get("output", 0),
                usage.get("total", 0),
                latency,
                self._estimate_cost(model, usage.get("input", 0), usage.get("output", 0)),
                status,
                error,
            )
        )
        self.conn.commit()

    def call(self, model, messages, **kwargs):
        trace_id = str(uuid.uuid4())[:8]
        prompt_preview = messages[-1]["content"] if messages else ""

        start = time.time()
        try:
            resp = self.client.chat.completions.create(model=model, messages=messages, **kwargs)
            latency = (time.time() - start) * 1000

            usage = {}
            if resp.usage:
                usage = {
                    "input": resp.usage.prompt_tokens,
                    "output": resp.usage.completion_tokens,
                    "total": resp.usage.total_tokens,
                }

            self._log(trace_id, model, prompt_preview, usage, latency, "success")

            content = resp.choices[0].message.content if resp.choices else None
            if content is None:
                content = "(empty response from model)"

            print(f"  [trace:{trace_id}] {model} | {latency:.0f}ms | "
                  f"{usage.get('total', 0)} tokens | ${self._estimate_cost(model, usage.get('input', 0), usage.get('output', 0)):.6f}")

            return content

        except Exception as e:
            latency = (time.time() - start) * 1000
            err_trace_id = trace_id + "-err"
            self._log(err_trace_id, model, prompt_preview, {}, latency, "error", str(e))
            print(f"  [trace:{trace_id}] ERROR | {latency:.0f}ms | {e}")
            raise

    def get_stats(self):
        rows = self.conn.execute("""
            SELECT
                COUNT(*) as total_calls,
                SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as successes,
                SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) as errors,
                AVG(latency_ms) as avg_latency,
                SUM(total_tokens) as total_tokens,
                SUM(cost_usd) as total_cost
            FROM traces
        """).fetchone()

        return {
            "total_calls": rows[0],
            "successes": rows[1],
            "errors": rows[2],
            "avg_latency_ms": round(rows[3] or 0, 1),
            "total_tokens": rows[4] or 0,
            "total_cost_usd": round(rows[5] or 0, 6),
            "error_rate": f"{(rows[2] or 0) / max(rows[0], 1) * 100:.1f}%",
        }

    def recent_traces(self, limit=5):
        return self.conn.execute(
            "SELECT id, model, latency_ms, total_tokens, status FROM traces ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        ).fetchall()


if __name__ == "__main__":
    tracer = LLMTracer()
    model = "nvidia/nemotron-3-super-120b-a12b:free"

    print("Making traced LLM calls...\n")

    tracer.call(model, [{"role": "user", "content": "What is Python?"}])
    tracer.call(model, [{"role": "user", "content": "Explain async/await in 2 sentences"}])
    tracer.call(model, [{"role": "user", "content": "What is FastAPI good for?"}])

    # intentional error
    try:
        tracer.call("nonexistent-model", [{"role": "user", "content": "test"}])
    except Exception:
        pass

    print("\n--- Stats ---")
    stats = tracer.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\n--- Recent Traces ---")
    for trace_id, m, latency, tokens, status in tracer.recent_traces():
        print(f"  [{trace_id}] {status} | {latency:.0f}ms | {tokens} tok | {m}")
