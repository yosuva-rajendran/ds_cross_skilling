import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENROUTER_API_KEY"), base_url="https://openrouter.ai/api/v1")

models_to_try = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "z-ai/glm-5.2:free",
]

tools = [{"type": "function", "function": {"name": "calc", "description": "Calculate math expression", "parameters": {"type": "object", "properties": {"expr": {"type": "string"}}}}}]

for m in models_to_try:
    try:
        resp = client.chat.completions.create(
            model=m,
            messages=[{"role": "user", "content": "What is 2+2? Use the calc tool."}],
            tools=tools,
            timeout=30,
        )
        tc = resp.choices[0].message.tool_calls
        content = resp.choices[0].message.content
        print(f"OK  {m}")
        print(f"    tool_calls={bool(tc)}, content={str(content)[:60]}")
    except Exception as e:
        print(f"ERR {m} -> {str(e)[:100]}")
