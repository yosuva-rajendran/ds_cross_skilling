**What Function Calling Is**
Function calling (also called "tool use") is a capability that lets an LLM interact with external code, APIs, or data sources in a structured way. Instead of just generating text, the model can output a structured request saying "call this function with these arguments," and the calling application executes that function and feeds the result back to the model.

The core problem it solves: LLMs are frozen at training time and can't natively query live data (today's weather, a database row, a stock price) or take actions (send an email, create a ticket, run code). Function calling bridges that gap by letting the model _describe_ what it wants to do, while your code does the actual doing.

Important nuance: the model never executes anything itself. It only produces structured output (usually JSON) describing an intended call. Your application layer is responsible for actually running the function and returning results.

### Function Calling vs. RAG vs. Plain Prompting

||Plain Prompting|RAG|Function Calling|
|---|---|---|---|
|**What it does**|Model answers from parameters (training data) only|Retrieves relevant documents/chunks and injects them into context before generation|Model requests a _live action or computation_, gets a result back, then answers|
|**Data freshness**|Frozen at training cutoff|As fresh as your retrieval index|As fresh as the live system it calls|
|**Best for**|General knowledge, reasoning, writing|Answering questions grounded in a large corpus (docs, wikis, manuals)|Actions and precise real-time data: math, DB lookups, sending messages, triggering workflows|
|**Determinism**|Model's own recall (can hallucinate)|Grounded in retrieved text, but retrieval quality varies|Deterministic — the function itself computes/fetches the real value|
|**Mechanism**|Prompt in, text out|Embed query → vector search → stuff top-k chunks into prompt → generate|Schema in → structured call out → execute → feed result back → generate|



