# LangGraph

LangGraph is a low-level orchestration framework for building stateful, multi-actor
applications with Large Language Models (LLMs). It is built on top of LangChain but is
framework-agnostic: you can use it with any LLM.

## Core concepts

- **Nodes**: Python functions (or runnables) that perform a single step of work. Each node
  receives the current state and returns an update to it.
- **Edges**: Connections between nodes that define the flow. There are normal edges and
  conditional edges, where a routing function decides the next node based on the state.
- **State**: A shared, mutable data structure (typically a `TypedDict`) that is passed
  between nodes. Channels define how updates are merged (e.g. `add_messages` for chat
  histories).
- **Graph**: The overall structure that wires nodes and edges together, then gets compiled.
- **Checkpointer**: Saves state between runs, enabling persistence, human-in-the-loop, and
  time-travel. `MemorySaver` keeps state in memory; `SqliteSaver` persists it to disk.
- **Streaming**: `graph.stream()` yields updates as nodes finish, and `astream_events()`
  yields fine-grained events for streaming tokens.

## Why use LangGraph

LangGraph gives you precise control over the control flow of an agent or pipeline. Unlike a
single linear chain, you can model loops (e.g. re-retrieving until relevance), branching,
and cycles with clear state management. It also makes graphs inspectable and debuggable by
visualising each step.

## Agent loop example

The `create_react_agent` helper from `langgraph.prebuilt` builds a tool-calling ReAct agent
with a built-in loop: the model calls a tool, the tool result is fed back, and the loop
continues until the model answers without calling tools.

## When to use LangGraph vs LangChain

- LangChain LCEL chains are great for linear or simple branched pipelines (prompt -> model -> parser).
- LangGraph is the right tool when you need cycles, conditional routing, state management,
  human-in-the-loop, or fine-grained control over the flow.
