import os
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)
MODEL = "nvidia/nemotron-3-super-120b-a12b:free"


def calculator(expression):
    try:
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "Error: invalid characters"
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"


def word_count(text):
    return str(len(text.split()))


def reverse_string(text):
    return text[::-1]


tools_registry = {
    "calculator": {"fn": calculator, "desc": "Evaluate math expressions like '2+2' or '(10*5)/2'"},
    "word_count": {"fn": word_count, "desc": "Count words in a text"},
    "reverse_string": {"fn": reverse_string, "desc": "Reverse a given string"},
}

SYSTEM_PROMPT = """You are a helpful assistant that solves problems step by step.

You have access to these tools:
{tools}

To use a tool, respond in this format:
Thought: <reasoning>
Action: <tool_name>
Action Input: <input>

When you have the final answer:
Thought: <reasoning>
Final Answer: <answer>

Rules:
- Always start with Thought
- One tool per step
- Wait for Observation before next step
"""


def get_tool_list():
    return "\n".join(f"- {name}: {t['desc']}" for name, t in tools_registry.items())


def parse_output(text):
    text = text.strip()
    if "Final Answer:" in text:
        return {"type": "final", "answer": text.split("Final Answer:")[-1].strip()}

    action = re.search(r"Action:\s*(.+)", text)
    action_input = re.search(r"Action Input:\s*(.+)", text)
    if action and action_input:
        return {"type": "action", "tool": action.group(1).strip(), "input": action_input.group(1).strip()}

    return {"type": "unknown", "raw": text}


def run_agent(query, max_steps=6):
    prompt = SYSTEM_PROMPT.format(tools=get_tool_list())
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": query},
    ]

    print(f"\nQuery: {query}")
    print("-" * 50)

    for step in range(max_steps):
        resp = client.chat.completions.create(model=MODEL, messages=messages, temperature=0, max_tokens=512)
        output = resp.choices[0].message.content
        print(f"\nStep {step+1}:\n{output}")

        parsed = parse_output(output)

        if parsed["type"] == "final":
            print(f"\n=> {parsed['answer']}")
            return parsed["answer"]

        elif parsed["type"] == "action":
            tool_name = parsed["tool"]
            tool_input = parsed["input"]

            if tool_name in tools_registry:
                obs = tools_registry[tool_name]["fn"](tool_input)
            else:
                obs = f"Error: no tool named '{tool_name}'. Available: {list(tools_registry.keys())}"

            print(f"Observation: {obs}")
            messages.append({"role": "assistant", "content": output})
            messages.append({"role": "user", "content": f"Observation: {obs}"})
        else:
            messages.append({"role": "assistant", "content": output})
            messages.append({"role": "user", "content": "Respond with Action or Final Answer."})

    return "Max steps reached."


if __name__ == "__main__":
    run_agent("What is (15 * 24) + (30 / 5)?")
    run_agent("How many words in 'the quick brown fox jumps over the lazy dog'? Square that number.")
    run_agent("Reverse the word 'artificial'")
