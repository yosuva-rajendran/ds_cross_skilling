# Module 14: Caching and Cost Optimization

## Why Cache LLM Calls?

- LLM calls are **slow** (2-30 seconds)
- LLM calls are **expensive** ($2-15 per million tokens)
- Many queries are similar or identical
- Caching can cut costs by 30-70% in production

## Exact-Match Caching

Hash the prompt → check cache → return if hit → call LLM if miss → store result.

```
User: "What is Python?"  →  hash("What is Python?")  →  cache miss  →  call LLM  →  store
User: "What is Python?"  →  hash("What is Python?")  →  cache HIT   →  return stored result
```

Simple, fast, zero false positives. But misses semantically similar queries:
- "What is Python?" vs "Explain Python" — same intent, different hash.

## Semantic Caching

Embed the query → search cache by vector similarity → return if close enough.

```
User: "Explain Python"  →  embed  →  similar to "What is Python?" (0.94)  →  cache HIT
User: "How to cook pasta" →  embed  →  no similar entry (0.12)  →  cache miss
```

Catches paraphrases. But needs a similarity threshold — too low and you get false hits.

| Strategy | Pros | Cons |
|----------|------|------|
| Exact match | Fast, no false positives | Misses paraphrases |
| Semantic | Catches similar queries | Needs embeddings, threshold tuning |
| Hybrid | Best coverage | More complex |

## Model Routing

Not every query needs GPT-4. Route by complexity:

- **Simple** (greetings, factual) → cheap/fast model (GPT-4o-mini, free model)
- **Medium** (summarization, Q&A) → mid-tier model
- **Complex** (reasoning, code, multi-step) → powerful model (GPT-4o, Claude)

### How to Classify
1. Rule-based: keyword matching, query length
2. LLM-based: ask a cheap model to classify complexity
3. Cascading: try cheap model first, escalate if confidence is low

## Prompt Compression

Reduce token count without losing meaning:
- Remove filler words and redundant context
- Summarize long documents before injecting
- Use abbreviations the model understands
- Tools: LLMLingua, LongLLMLingua

## TTL and Invalidation

- Set time-to-live on cached responses (1 hour, 1 day, etc.)
- Invalidate when underlying data changes
- Version cache keys when prompts change
- Monitor cache hit rate — low rate means cache isn't helping

## Cost Tracking

Track per request: `cost = (input_tokens * input_rate + output_tokens * output_rate) / 1M`

Set budgets per user, per project, per day. Alert when approaching limits.
