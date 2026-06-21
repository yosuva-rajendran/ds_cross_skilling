
**Rate limits — RPM and TPM**
- **RPM** — _requests per minute_: how many calls you may make.
- **TPM** — _tokens per minute_: how many tokens you may process.

**What streaming is**

**Streaming** instead sends the response incrementally,  small chunks of text as each is produced  over a single long-lived connection.

**Server-Sent Events (SSE)**

Streaming is delivered using **Server-Sent Events**, a standard for pushing a stream of events from server to client over one HTTP connection.

- It's **one-way** (server → client) and runs over plain HTTP. That's different from **WebSockets**, which are bidirectional. LLM streaming only needs server → client, so SSE fits.

**Context window limits**

The context window is the maximum number of tokens — **input plus output combined** — that a model can handle in one request. if a model has a 200K context window and you fill 199K with input, you've left almost nothing for the response. Different models have different windows (some are 128K, some 200K, some 1M), and they differ by _provider and model version_.

**Sliding window strategy**

The **sliding window** strategy is a way of keeping a conversation's token count under control by only keeping the most recent part of the history and discarding the rest.