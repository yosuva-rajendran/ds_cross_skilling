
import argparse
import os
import sys
from dotenv import load_dotenv
from groq import Groq
from agent_loop import run_agent_loop
from tools.registry import get_tools

SYSTEM_PROMPT = (
    "You are a helpful support assistant. Use the available tools whenever they would give a more accurate or up-to-date answer than your own "
    "knowledge -- especially for weather, current events, order lookups, "
    "and arithmetic. Do not claim to have done something (like searching "
    "or deleting an order) unless you actually called the corresponding tool."
)


def main():
    # Windows consoles default to cp1252, which crashes on some model output.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Groq tool-calling agent (backend CLI)")
    parser.add_argument("--model", help="Model to use (default: GROQ_MODEL env or llama-3.3-70b-versatile)")
    args = parser.parse_args()

    load_dotenv()
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise SystemExit("Set GROQ_API_KEY in your environment or .env file (see .env.example).")

    model = args.model or os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    client = Groq(api_key=api_key)
    tools = get_tools()

    print("Type 'exit' to quit.\n")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        user_input = input("you> ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})
        answer = run_agent_loop(client, model, messages, tools)
        print(f"\nagent> {answer}\n")


if __name__ == "__main__":
    main()
