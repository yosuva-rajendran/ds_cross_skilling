# Module 13: Observability and Monitoring

## Why Observability for LLMs?

LLM outputs are non-deterministic. Same input can give different outputs.
You can't just write unit tests and call it a day. You need visibility into:

- What prompt was sent?
- What did the model return?
- How long did it take?
- How many tokens were used?
- How much did it cost?
- Did the user find it useful?

Without this, you're flying blind in production.

## What to Track

### Latency
- **TTFT** (Time to First Token) — how fast streaming starts
- **Total generation time** — full response time
- Track per endpoint, per model, over time

### Token Usage
- Input tokens (prompt)
- Output tokens (response)
- Total tokens
- This directly maps to cost

### Cost
- Per request
- Per user
- Per feature/endpoint
- Per model (if routing across models)

### Errors
- API errors (rate limit, timeout, 500s)
- Tool execution failures
- Content policy violations
- Parsing errors (malformed JSON from LLM)

### Quality (harder to measure)
- Retrieval relevance scores (for RAG)
- User thumbs up/down
- Hallucination rate

## Logging Best Practices

1. **Structured JSON logs** — not plain text
2. **Correlation ID** — trace a request across services
3. **Scrub PII** before logging (names, emails, etc.)
4. **Log levels** — DEBUG for full prompts (dev only), INFO for metrics, ERROR for failures
5. **Don't log full prompts in production** unless you have PII controls

## Tools

### LangSmith
- Automatic tracing for LangChain/LangGraph
- Trace explorer — see every step of an agent
- Datasets and eval runs
- Prompt versioning

### Langfuse
- Open source, self-hostable
- Works with any LLM (not tied to LangChain)
- Python decorator for easy tracing
- Cost dashboards, latency charts
- Prompt management

### Custom Logging
- Wrap your LLM calls with timing + token counting
- Store in SQLite/Postgres for analysis
- Build dashboards with Grafana, Streamlit, etc.
- Good enough for learning and small projects

## Key Metrics Dashboard

| Metric | What It Tells You |
|--------|-------------------|
| p50/p95 latency | Typical vs worst-case response time |
| Tokens per request | Are prompts bloating over time? |
| Cost per day | Budget tracking |
| Error rate | System health |
| Cache hit rate | Are you saving money? |
