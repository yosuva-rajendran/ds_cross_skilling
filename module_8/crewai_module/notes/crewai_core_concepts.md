# CrewAI - Core Concepts Notes

## 1. What is CrewAI?

A Python framework for orchestrating **autonomous AI agents** that collaborate to solve complex tasks.

**Mental Model:** Like assembling a team of specialists - each has a role, a goal, and tools.

---

## 2. Agents

An Agent is an autonomous unit powered by an LLM.

**Required fields:**
| Field | Purpose |
|-------|---------|
| `role` | Job title (e.g., "Data Analyst") |
| `goal` | What the agent aims to achieve |
| `backstory` | Context shaping behavior & personality |

**Optional fields:**
| Field | Default | Purpose |
|-------|---------|---------|
| `llm` | gpt-4o | Which model to use |
| `tools` | [] | List of tools agent can use |
| `verbose` | False | Show reasoning steps |
| `allow_delegation` | False | Can delegate to other agents |
| `memory` | False | Remember past interactions |
| `max_iter` | 25 | Max reasoning iterations |
| `max_rpm` | None | Rate limit API calls |

**Example:**
```python
from crewai import Agent

researcher = Agent(
    role="Market Researcher",
    goal="Find accurate market data and trends",
    backstory="Expert researcher with 10 years in tech industry.",
    llm="openrouter/openai/gpt-4o",
    verbose=True,
)
```

---

## 3. Tasks

A Task is a specific assignment given to an Agent.

**Required fields:**
| Field | Purpose |
|-------|---------|
| `description` | Detailed instructions (be specific!) |
| `expected_output` | What the result should look like |
| `agent` | Who does the work |

**Optional fields:**
| Field | Purpose |
|-------|---------|
| `context` | List of tasks whose outputs feed into this one |
| `tools` | Task-specific tools (overrides agent tools) |
| `output_file` | Save output to a file |
| `output_pydantic` | Force structured output (Pydantic model) |
| `human_input` | Pause for human review |
| `async_execution` | Run asynchronously |

**Example:**
```python
from crewai import Task

research_task = Task(
    description="Research the topic '{topic}'. Find 5 key points with data.",
    expected_output="Summary with 5 key points and supporting statistics.",
    agent=researcher,
)

# Task chaining - analysis_task gets research_task output automatically
analysis_task = Task(
    description="Analyze the research and provide recommendations.",
    expected_output="3 actionable recommendations with reasoning.",
    agent=analyst,
    context=[research_task],
)
```

---

## 4. Crews

A Crew is a team of Agents executing Tasks together.

**Process types:**
| Process | How it works | Use when |
|---------|-------------|----------|
| `sequential` | Tasks run in order (A → B → C) | Clear pipeline, each step depends on previous |
| `hierarchical` | Manager delegates to agents | Complex coordination needed |

**Key parameters:**
| Field | Purpose |
|-------|---------|
| `agents` | List of agents |
| `tasks` | List of tasks |
| `process` | sequential or hierarchical |
| `memory` | Enable crew-level memory |
| `verbose` | Show execution details |
| `planning` | Create plan before executing |

**Execution:**
```python
from crewai import Crew, Process

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential,
    verbose=True,
)

# Run it
result = crew.kickoff(inputs={"topic": "AI Agents"})
print(result.raw)          # String output
print(result.token_usage)  # Token metrics

# Batch run
results = crew.kickoff_for_each(inputs=[
    {"topic": "AI"}, {"topic": "ML"}, {"topic": "NLP"}
])
```

---

## 5. Tools

Tools let agents **interact with the world** (search, read, compute).

**Built-in tools** (install with `pip install 'crewai[tools]'`):
- `SerperDevTool` - Web search
- `ScrapeWebsiteTool` - Scrape websites
- `FileReadTool` / `FileWriterTool` - File operations
- `PDFSearchTool` / `CSVSearchTool` - Search documents
- `CodeInterpreterTool` - Execute Python code

**Custom tool with @tool decorator:**
```python
from crewai.tools import tool

@tool("Calculator")
def calculator(expression: str) -> str:
    """Evaluate a math expression.
    
    Args:
        expression: A math expression like '2 + 2' or '100 * 0.15'
    """
    return str(eval(expression))
```

**Custom tool with BaseTool class (for complex input):**
```python
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    query: str = Field(description="Search query")
    max_results: int = Field(default=5, description="Max results")

class MySearchTool(BaseTool):
    name: str = "Custom Search"
    description: str = "Search for information"
    args_schema: type = SearchInput

    def _run(self, query: str, max_results: int = 5) -> str:
        # your logic here
        return f"Results for: {query}"
```

**Assigning tools:**
```python
# Agent-level (available for all tasks)
agent = Agent(role="...", tools=[calculator, search_tool])

# Task-level (overrides agent tools for this task only)
task = Task(description="...", tools=[specific_tool], agent=agent)
```

---

## 6. Memory & Knowledge

### Memory (auto-generated from execution)

| Type | What it stores | Lifetime |
|------|---------------|----------|
| Short-term | Current run context | Single execution |
| Long-term | Patterns & insights | Across all runs |
| Entity | Facts about people/orgs | Across all runs |

**Storage:** LanceDB (local files at `.crewai/memory/`)

**Enable:**
```python
crew = Crew(
    agents=[...],
    tasks=[...],
    memory=True,  # That's it!
)
```

### Knowledge (you provide it)

Feed external facts to agents. Stored in ChromaDB locally.

```python
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource

company_info = StringKnowledgeSource(
    content="Company: Acme. Product: AI Platform. Pricing: $99/mo."
)

crew = Crew(
    agents=[...],
    tasks=[...],
    knowledge_sources=[company_info],
)
```

**File-based sources:** `TextFileKnowledgeSource`, `PDFKnowledgeSource`, `CSVKnowledgeSource`

---

## 7. Using OpenRouter

Set in `.env`:
```
OPENROUTER_API_KEY=sk-or-v1-xxxxx
```

Use in agents:
```python
agent = Agent(
    role="...",
    llm="openrouter/openai/gpt-4o",           # GPT-4o
    # llm="openrouter/anthropic/claude-sonnet-4-20250514",  # Claude
    # llm="openrouter/google/gemini-2.5-pro",    # Gemini
    # llm="openrouter/deepseek/deepseek-chat",   # DeepSeek
)
```

---

## Quick Reference Diagram

```
CREW (orchestrates)
├── AGENT 1 (role + goal + tools) → TASK 1
├── AGENT 2 (role + goal + tools) → TASK 2 (gets Task 1 output via context)
└── AGENT 3 (role + goal + tools) → TASK 3 (gets Task 2 output via context)

+ Memory (learns across runs)
+ Knowledge (reference facts you provide)
```
