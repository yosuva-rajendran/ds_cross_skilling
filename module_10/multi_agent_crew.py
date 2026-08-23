import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

load_dotenv()

llm = LLM(
    model="openrouter/nvidia/nemotron-3-super-120b-a12b:free",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)


@tool("Web Research")
def web_research(query: str) -> str:
    """Search for information on a given topic and return findings."""
    # simulated search results for demo purposes
    data = {
        "python web frameworks 2026": "FastAPI dominates new projects (42% adoption). Django still leads enterprise (38%). Flask declining. Litestar gaining traction. ASGI is the standard.",
        "frontend frameworks 2026": "React maintains lead (39%). Next.js is default for React apps. Svelte growing fast (15% YoY). Vue stable. HTMX popular for backend devs.",
        "database trends 2026": "PostgreSQL is the default choice. Vector DBs (Pinecone, Weaviate) mainstream for AI apps. SQLite for edge/embedded. Redis for caching. DuckDB for analytics.",
        "devops trends 2026": "Platform engineering replacing raw DevOps. Kubernetes still dominant. AI-assisted CI/CD pipelines. Infrastructure as Code standard. GitOps widespread.",
        "ai integration trends 2026": "RAG is standard pattern. Agents in production. Multi-modal APIs common. Local models viable for simple tasks. Fine-tuning commoditized.",
    }
    for key, val in data.items():
        if any(word in query.lower() for word in key.split()):
            return val
    return f"No specific data found for '{query}'"


@tool("Trend Scorer")
def trend_scorer(technology: str, metrics: str) -> str:
    """Score a technology on adoption, growth, job demand. Pass 3 comma-separated numbers (1-10)."""
    scores = [int(x.strip()) for x in metrics.split(",")]
    avg = sum(scores) / len(scores)
    verdict = "HOT" if avg >= 7 else "STABLE" if avg >= 5 else "DECLINING"
    parts = []
    for label, s in zip(["Adoption", "Growth", "Jobs"], scores):
        parts.append(f"{label}:{s}")
    return f"{technology} → {verdict} ({', '.join(parts)}, avg {avg:.1f})"


@tool("Comparison Table")
def comparison_table(items: str, criteria: str) -> str:
    """Build a markdown comparison table. Items and criteria are comma-separated."""
    cols = [c.strip() for c in criteria.split(",")]
    rows = [i.strip() for i in items.split(",")]
    table = "| Tech | " + " | ".join(cols) + " |\n"
    table += "|---" * (len(cols) + 1) + "|\n"
    for r in rows:
        table += f"| {r} | " + " | ".join(["—"] * len(cols)) + " |\n"
    return table


researcher = Agent(
    role="Tech Researcher",
    goal="Find current data on technology trends — adoption numbers, growth rates, who's using what",
    backstory="Senior tech analyst. You deal in facts and numbers, not hype. 10 years tracking industry shifts.",
    tools=[web_research],
    llm=llm,
    verbose=True,
)

analyst = Agent(
    role="Trend Analyst",
    goal="Score and rank technologies based on research data",
    backstory="You quantify everything. If there's no number, it's not an insight. You've built scoring models for 50+ tech evaluations.",
    tools=[trend_scorer, comparison_table],
    llm=llm,
    verbose=True,
)

writer = Agent(
    role="Report Writer",
    goal="Turn raw research and scores into a readable tech radar report",
    backstory="You write for busy engineering managers. Short paragraphs, bullet points, clear recommendations. No fluff.",
    llm=llm,
    verbose=True,
)

reviewer = Agent(
    role="Editor",
    goal="Check the report for accuracy and completeness before publishing",
    backstory="Picky editor. You catch unsupported claims, missing context, and vague recommendations. 200+ reports reviewed.",
    llm=llm,
    verbose=True,
)


research_task = Task(
    description="Research these 5 areas using the Web Research tool:\n"
                "1. Python backend frameworks\n"
                "2. Frontend frameworks\n"
                "3. Databases\n"
                "4. DevOps and deployment\n"
                "5. AI integration patterns\n\n"
                "Get real numbers — adoption %, growth, key players for each.",
    expected_output="Research findings for all 5 areas with data points and stats.",
    agent=researcher,
)

analysis_task = Task(
    description="Take the research and:\n"
                "- Score each major tech with Trend Scorer (adoption, growth, jobs each 1-10)\n"
                "- Build a comparison table of the top 5-6 technologies\n"
                "- Pick top 3 must-learn and top 3 watch-closely techs",
    expected_output="Scored technologies, comparison table, must-learn and watch lists.",
    agent=analyst,
    context=[research_task],
)

writing_task = Task(
    description="Write the Tech Radar Report 2026. Sections:\n"
                "- Executive Summary (3 lines max)\n"
                "- Findings by category (bullets)\n"
                "- Scores table\n"
                "- Recommendations: learn / drop / watch\n"
                "- 3 action items for a mid-level dev\n\n"
                "Under 800 words total.",
    expected_output="Complete tech radar report, all sections, under 800 words.",
    agent=writer,
    context=[research_task, analysis_task],
)

review_task = Task(
    description="Review the report. Check:\n"
                "- Claims backed by data?\n"
                "- Recommendations specific enough to act on?\n"
                "- Anything missing?\n"
                "- Tone right for engineering audience?\n\n"
                "Give PASS or NEEDS REVISION with specifics.",
    expected_output="PASS or NEEDS REVISION verdict with feedback.",
    agent=reviewer,
    context=[writing_task, research_task],
    output_file="outputs/tech_radar_review.md",
)


crew = Crew(
    agents=[researcher, analyst, writer, reviewer],
    tasks=[research_task, analysis_task, writing_task, review_task],
    process=Process.sequential,
    verbose=True,
)


if __name__ == "__main__":
    print("Running Tech Radar crew...\n")
    result = crew.kickoff()
    print("\n\nFinal output:\n")
    print(result.raw)
