# Module 9: Single Agent Systems - Core Concepts

## 1. What is an AI Agent?

An AI agent is a program that uses an LLM to **decide what to do next** in a loop, rather than following a fixed sequence.

```
Simple LLM Call:  Input → LLM → Output (one shot, done)
Chain:            Input → LLM → Tool → LLM → Output (fixed sequence)
Agent:            Input → [LLM decides → Act → Observe → Repeat] → Output (dynamic loop)
```

### Agent vs LLM Call vs Chain

| | LLM Call | Chain | Agent |
|---|---|---|---|
| Steps | 1 | Fixed N | Dynamic (agent decides) |
| Tools | No | Pre-defined order | Agent picks which tool, when |
| Logic | None | Hardcoded | LLM reasons at each step |
| Use when | Simple Q&A | Known workflow | Open-ended problems |

### When to Use an Agent

**Use agent when:**
- The number of steps isn't known in advance
- The tool to use depends on intermediate results
- The problem requires reasoning + acting together

**Use fixed pipeline when:**
- Steps are always the same
- Latency/cost must be predictable
- Reliability is more important than flexibility

### Limitations of Single Agents

- **Reliability** - LLM can hallucinate tool calls or loop forever
- **Latency** - Each loop iteration = 1 LLM call + tool execution
- **Cost** - More iterations = more tokens = more money
- **Context overflow** - Long scratchpads can exceed token limits

---

## 2. The Agent Loop

```
         ┌──────────────────────────────────┐
         │                                  │
         ▼                                  │
    [Perceive]  ← receive input/observation │
         │                                  │
         ▼                                  │
    [Think]     ← LLM reasons what to do    │
         │                                  │
         ▼                                  │
    [Act]       ← call a tool or respond    │
         │                                  │
         ▼                                  │
    [Observe]   ← get tool result ──────────┘
         │
         ▼ (if done)
    [Final Answer]
```

---

## 3. Agent Architecture - Components

| Component | Role |
|-----------|------|
| **LLM Brain** | Reasons, decides next action, generates final answer |
| **Tools** | Functions the agent can call (search, calculate, read file) |
| **Memory** | Conversation history + past observations |
| **Executor** | Runtime that manages the loop (call LLM, run tool, repeat) |
| **Scratchpad** | Running log of Thought → Action → Observation steps |
| **Stop Condition** | When agent says "Final Answer" or hits max iterations |

### System Prompt Design

The system prompt tells the agent:
1. What it is (role)
2. What tools it has (names, descriptions, parameters)
3. How to format actions (so executor can parse them)
4. When to stop (produce final answer)

### Tool Registry

Tools are described to the LLM so it can pick which one to use:
```python
tools = [
    {
        "name": "calculator",
        "description": "Evaluate math expressions",
        "parameters": {"expression": "string"}
    },
    {
        "name": "web_search", 
        "description": "Search the internet for current information",
        "parameters": {"query": "string"}
    }
]
```

The LLM sees these descriptions and decides which tool fits the current need.

---

## 4. ReAct Pattern (Reasoning + Acting)

The most fundamental agent pattern. Interleaves thinking with action.

```
Loop:
  Thought: "I need to find the current price of AAPL stock"
  Action: web_search("AAPL stock price today")
  Observation: "AAPL is trading at $198.50"
  
  Thought: "Now I need to calculate 10% of that for the commission"
  Action: calculator("198.50 * 0.10")
  Observation: "19.85"
  
  Thought: "I have all the info. Commission on 100 shares = $1985"
  Final Answer: "The 10% commission on 100 shares of AAPL at $198.50 is $1,985.00"
```

### Why ReAct works

- **Thought** = reasoning trace (makes LLM more accurate)
- **Action** = grounding in real tools (prevents hallucination)
- **Observation** = real data fed back (corrects course)

---

## 5. OpenAI Tools Agent (Function Calling)

Instead of parsing text for actions, OpenAI models natively output structured tool calls.

```python
# LLM response includes structured tool_calls:
{
    "tool_calls": [
        {
            "function": {
                "name": "web_search",
                "arguments": "{\"query\": \"AAPL price\"}"
            }
        }
    ]
}
```

**Advantage:** No text parsing needed. LLM outputs exact function name + JSON args.

---

## 6. LangGraph Single Agent

Models the agent loop as a **graph**:

```
[Start] → [Call LLM] → (should_continue?) → [Call Tool] → [Call LLM] → ...
                              │
                              └── (done) → [End]
```

Components:
- **State**: Holds messages + scratchpad
- **Node "agent"**: Calls the LLM
- **Node "tools"**: Executes the tool
- **Conditional Edge**: If LLM returned tool_calls → go to tools node, else → end

---

## 7. Agent Memory

| Type | What | How |
|------|------|-----|
| **Short-term** | Current conversation + scratchpad | Passed in messages list |
| **Tool results** | Output of each tool call | Appended as "observation" message |
| **Step state** | Intermediate values across iterations | Kept in state dict |
| **Long-term** | Past conversations, facts | External vector store |

---

## 8. Error Handling & Reliability

| Problem | Solution |
|---------|----------|
| Infinite loop | `max_iterations` limit (e.g., 10) |
| Invalid tool call | Catch exception, feed error back to LLM as observation |
| Tool timeout | Set timeout per tool call (e.g., 30s) |
| LLM hallucinated tool name | Validate against registered tools, return error message |
| Context overflow | Summarize old scratchpad entries |

---

## 9. Agent Evaluation

| Metric | What it measures |
|--------|-----------------|
| **Task completion** | Did the agent produce the correct final answer? |
| **Trajectory** | Were the right tools called in the right order? |
| **Step efficiency** | Did it solve in minimum steps (no unnecessary calls)? |
| **Cost** | Total tokens used across all iterations |
| **Latency** | Wall-clock time from start to final answer |

Tools: LangSmith for tracing, manual review of agent trajectories.

---

## Quick Comparison: Frameworks for Single Agents

| Framework | How to Build Agent |
|-----------|-------------------|
| **From scratch** | While loop + LLM call + tool execution |
| **LangChain** | `create_tool_calling_agent` + `AgentExecutor` |
| **LlamaIndex** | `ReActAgent` or `OpenAIAgent` |
| **LangGraph** | Graph with "agent" node + "tools" node + conditional edge |
