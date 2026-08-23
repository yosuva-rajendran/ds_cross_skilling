import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool

load_dotenv()

llm = ChatOpenAI(
    model="nvidia/nemotron-3-super-120b-a12b:free",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)


@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression. Use for any calculations."""
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return "Error: invalid characters"
    return str(eval(expression))


@tool
def word_count(text: str) -> str:
    """Count the number of words in given text."""
    return str(len(text.split()))


@tool
def reverse_string(text: str) -> str:
    """Reverse the given string and return it."""
    return text[::-1]


tools = [calculator, word_count, reverse_string]

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="You are a helpful assistant. Use tools when needed.",
)


if __name__ == "__main__":
    print("\n[Test 1] Math")
    result = agent.invoke({"messages": [{"role": "user", "content": "What is (15 * 24) + (30 / 5)?"}]})
    print(f"Answer: {result['messages'][-1].content}")

    print("\n[Test 2] Multi-step")
    result = agent.invoke({"messages": [{"role": "user", "content": "Count words in 'the quick brown fox jumps over the lazy dog' and square it"}]})
    print(f"Answer: {result['messages'][-1].content}")

    print("\n[Test 3] String")
    result = agent.invoke({"messages": [{"role": "user", "content": "Reverse the word 'artificial'"}]})
    print(f"Answer: {result['messages'][-1].content}")
