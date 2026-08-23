# Module 10: Multi-Agent Systems

## Why Multi-Agent Over Single-Agent?

A single agent handles everything — planning, executing, verifying. Works fine for simple tasks.
But when complexity grows, a single agent hits walls:

- **Context window overload** — one agent juggling research + writing + code + review runs out of space
- **No specialization** — a generalist prompt can't match a focused expert prompt
- **No parallelism** — one agent = sequential execution, always
- **No self-correction** — an agent rarely catches its own mistakes

Multi-agent solves this by splitting work across specialists that coordinate.

| Dimension | Single Agent | Multi-Agent |
|-----------|-------------|-------------|
| Task complexity | Simple, linear | Complex, branching |
| Execution | Sequential only | Parallel possible |
| Quality control | Self-review (weak) | Separate reviewer (strong) |
| Context usage | Bloated with everything | Each agent gets focused context |
| Failure recovery | Retry same approach | Fallback to different agent |

**When to stay single-agent:** simple tool use, straightforward Q&A, one-step tasks.
**When to go multi-agent:** research + synthesis, code + review, plan + execute + verify.

---

## Agent Roles

### Planner Agent
Breaks a high-level goal into concrete sub-tasks. Decides execution order and dependencies.
Does NOT execute — only plans.

### Executor Agent
Takes a specific sub-task and completes it. Has access to tools. Focused, narrow scope.
Multiple executors can run in parallel on independent tasks.

### Critic / Reviewer Agent
Reviews output from executors. Checks correctness, completeness, quality.
Can approve, reject, or request revisions. Key for self-correction.

### Researcher Agent
Gathers information — searches web, reads documents, pulls data.
Feeds findings to other agents. No decision-making, just retrieval.

### Writer / Generator Agent
Produces final output — reports, code, summaries.
Takes structured input from researchers/planners and crafts polished output.

### Orchestrator / Supervisor Agent
Top-level coordinator. Routes tasks to the right agent. Decides when work is done.
Doesn't do the work — manages who does what and when.

---

## Communication Patterns

### Hub-and-Spoke (Supervisor)
One central supervisor routes messages to worker agents. Workers only talk to the supervisor.

```
        Supervisor
       /    |    \
    Agent  Agent  Agent
```

- Simple to reason about
- Supervisor is the bottleneck
- Most common pattern in practice (CrewAI hierarchical, LangGraph supervisor)

### Peer-to-Peer
Agents communicate directly with each other. No central coordinator.

```
    Agent <---> Agent
      ^           ^
       \         /
        v       v
         Agent
```

- Flexible, no bottleneck
- Hard to debug, can lead to infinite loops
- Good for brainstorming/debate scenarios

### Hierarchical
Multi-level management. Top supervisor delegates to mid-level supervisors who manage workers.

```
    CEO Agent
    /       \
  Manager   Manager
  /    \       \
Worker Worker Worker
```

- Scales to complex systems
- Each level reduces scope
- Production-grade pattern

### Blackboard (Shared State)
All agents read/write to a shared state object. No direct messaging.

```
    Agent --> [Shared State] <-- Agent
                   ^
                   |
                 Agent
```

- Decoupled agents
- Easy to add/remove agents
- State management is the challenge
- LangGraph's state graph is essentially this

### Pipeline (Linear Handoff)
Each agent passes output to the next. Like an assembly line.

```
    Research --> Analyze --> Write --> Review --> Output
```

- Simple, predictable flow
- No parallelism
- Good for sequential workflows (CrewAI sequential process)

---

## Task Decomposition

### Breaking Goals Into Sub-Tasks

A planner agent receives: "Write a market analysis report on EV industry"

Decomposes into:
1. Research current EV market size and growth
2. Identify top 5 players and market share
3. Analyze recent trends (policy, tech, consumer)
4. Compile findings into structured report
5. Review for accuracy and completeness

### Dependency Graphs

Some tasks depend on others:

```
Task 1 (Research) ─┐
                   ├──> Task 4 (Compile)──> Task 5 (Review)
Task 2 (Players) ──┘        ^
                             |
Task 3 (Trends) ─────────────┘
```

Tasks 1, 2, 3 are independent → can run in parallel.
Task 4 needs all three → must wait.
Task 5 needs Task 4 → sequential.

### Parallel vs Sequential

**Sequential:** Simpler, deterministic, easier to debug. Use when tasks depend on each other.

**Parallel:** Faster, but needs result merging. Use when tasks are independent.

In LangGraph: use `Send()` to fan out to multiple nodes, then merge in a collector node.

### Merging Results

When parallel agents finish, a merge step combines their outputs:
- Concatenation (simple append)
- Summarization (LLM condenses)
- Structured merge (fill sections of a template)
- Conflict resolution (if agents disagree, supervisor decides)

---

## Reliability Patterns

### Retry Logic
```python
max_retries = 3
for attempt in range(max_retries):
    result = agent.invoke(task)
    if is_valid(result):
        break
    # Modify prompt with error feedback and retry
```

### Timeouts
Set maximum time for any single tool call or agent step. Kill and retry if exceeded.
Prevents hung API calls from blocking the entire system.

### Fallback Agents
If primary agent fails repeatedly, route to a different agent (maybe simpler, maybe different model).
Example: if GPT-4 agent fails, fall back to Claude agent with same prompt.

### Guardrails on Output
Validate agent output before passing downstream:
- Schema validation (JSON structure, required fields)
- Content checks (no hallucinated data, within expected ranges)
- Length limits (prevent token explosion)
- Safety filters (no harmful content)

### Max Iteration Limits
Hard cap on how many times an agent can loop. Prevents infinite cycles.
Typical: 10-25 iterations max. If not done by then, escalate or fail gracefully.

### Logging Every Step
Record every agent decision, tool call, and output. Essential for debugging.
Use LangSmith, custom loggers, or structured logging to trace execution paths.

---

## Human-in-the-Loop

### When to Pause for Approval
- Before executing irreversible actions (delete, send email, deploy)
- When confidence is low (agent is uncertain)
- At plan stage (show plan, get approval before execution)
- When cost is high (expensive API calls, large operations)

### Interrupting a LangGraph Workflow
LangGraph supports `interrupt_before` and `interrupt_after` on nodes:

```python
graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["execute_action"]
)
```

When the graph hits that node, it pauses. Human reviews the state, then resumes or modifies.

### Presenting Plan Before Execution
1. Planner agent generates plan
2. System pauses and shows plan to user
3. User approves / edits / rejects
4. If approved, executors proceed
5. If rejected, planner revises

### Accepting, Rejecting, or Editing Steps
After interruption, the human can:
- **Accept** — resume execution as-is
- **Reject** — terminate or re-plan
- **Edit** — modify the state (change tool inputs, adjust parameters) then resume

### Audit Trail
Every agent decision is logged with:
- Timestamp
- Agent name/role
- Input received
- Decision made (tool call, message, etc.)
- Output produced
- Human intervention (if any)

This creates full traceability for compliance, debugging, and improvement.

---

## Key Takeaways

1. Multi-agent shines when tasks need specialization, parallelism, or self-correction
2. Start with supervisor pattern — simplest to implement and debug
3. Add parallelism only where tasks are truly independent
4. Always have a reviewer agent — self-correction is the main benefit
5. Set max iterations and timeouts — agents will loop forever without them
6. Log everything — you can't debug what you can't see
7. Human-in-the-loop for anything irreversible or high-stakes
