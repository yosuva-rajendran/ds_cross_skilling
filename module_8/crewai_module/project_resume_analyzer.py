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


@tool("Skill Matcher")
def skill_matcher(resume_skills: str, required_skills: str) -> str:
    """Compare resume skills against job requirements and find gaps.

    Args:
        resume_skills: Comma-separated skills from the resume
        required_skills: Comma-separated skills required by the job
    """
    resume_set = {s.strip().lower() for s in resume_skills.split(",")}
    required_set = {s.strip().lower() for s in required_skills.split(",")}

    matched = resume_set & required_set
    missing = required_set - resume_set
    extra = resume_set - required_set
    match_percent = len(matched) / len(required_set) * 100 if required_set else 0

    return (
        f"Match Score: {match_percent:.0f}%\n"
        f"Matched ({len(matched)}): {', '.join(sorted(matched)) or 'None'}\n"
        f"Missing ({len(missing)}): {', '.join(sorted(missing)) or 'None'}\n"
        f"Extra ({len(extra)}): {', '.join(sorted(extra)) or 'None'}"
    )


@tool("Experience Calculator")
def experience_calculator(years: str, required_years: str) -> str:
    """Compare candidate experience against job requirements.

    Args:
        years: Candidate's years of experience (e.g., "3")
        required_years: Required years of experience (e.g., "5")
    """
    candidate = float(years)
    required = float(required_years)
    diff = candidate - required

    if diff >= 0:
        status = "MEETS REQUIREMENT"
    elif diff >= -1:
        status = "SLIGHTLY BELOW"
    else:
        status = "BELOW REQUIREMENT"

    return f"{status} | Candidate: {candidate:.0f}yr | Required: {required:.0f}yr"


resume_analyst = Agent(
    role="Resume Analyst",
    goal="Analyze resumes against job descriptions to identify strengths and gaps",
    backstory=(
        "Career coach with 15 years of experience. Honest about gaps but constructive. "
        "You use STAR method principles and always quantify achievements."
    ),
    tools=[skill_matcher, experience_calculator],
    llm=llm,
    verbose=True,
)

interview_coach = Agent(
    role="Interview Coach",
    goal="Prepare candidates with tailored interview questions and strategies",
    backstory=(
        "Interview coach who has helped 500+ candidates prepare for tech interviews. "
        "You recommend STAR method for answers, suggest quantifying achievements, "
        "and advise preparing 3-5 questions for the interviewer."
    ),
    llm=llm,
    verbose=True,
)

analysis_task = Task(
    description=(
        "Analyze this resume against the job description.\n\n"
        "RESUME:\n{resume}\n\n"
        "JOB DESCRIPTION:\n{job_description}\n\n"
        "Use Skill Matcher tool to compare skills. "
        "Use Experience Calculator to check experience fit."
    ),
    expected_output=(
        "Overall fit score (Strong/Moderate/Weak), "
        "skill match results, experience assessment, "
        "top 3 strengths, top 3 gaps"
    ),
    agent=resume_analyst,
)

interview_prep_task = Task(
    description=(
        "Based on the resume analysis, create interview preparation guide with "
        "5 likely interview questions tailored to the role, "
        "answer framework for each, "
        "3 things to highlight from candidate background, "
        "2 areas to prepare for where gaps exist"
    ),
    expected_output="Interview prep guide with questions, frameworks, highlights, and prep areas.",
    agent=interview_coach,
    context=[analysis_task],
    output_file="outputs/interview_prep.md",
)

resume_crew = Crew(
    agents=[resume_analyst, interview_coach],
    tasks=[analysis_task, interview_prep_task],
    process=Process.sequential,
    verbose=True,
)


if __name__ == "__main__":
    sample_resume = """
    Name: Yosuva R
    Experience: 3 years
    Current Role: Junior Data Scientist at TechCorp
    Skills: Python, Pandas, Scikit-learn, SQL, Power BI, Machine Learning,
            NLP basics, FastAPI, LangChain, RAG, Git
    Education: B.Tech in Computer Science
    Projects:
    - Built a RAG-based document QA system using LangChain + ChromaDB
    - Created ML pipeline for customer churn prediction (92% accuracy)
    - Developed semantic search engine with sentence transformers
    """

    sample_job = """
    Role: AI/ML Engineer
    Company: InnovateAI
    Experience Required: 3-5 years
    Required Skills: Python, Machine Learning, Deep Learning, NLP,
                     LLMs, RAG, Vector Databases, Docker, AWS,
                     MLOps, CI/CD, TensorFlow/PyTorch
    Nice to have: CrewAI, Multi-agent systems, Kubernetes
    """

    print("Running Resume Analyzer Crew...")
    result = resume_crew.kickoff(inputs={
        "resume": sample_resume,
        "job_description": sample_job,
    })

    print("\nResult:")
    print(result.raw)
