import json
from concurrent.futures import ThreadPoolExecutor

from groq import BadRequestError

from tools.registry import get_executor

MAX_TURNS = 8


def _create_completion(client, model, messages, tools):
    """Call the model, retrying Groq's transient tool-call 400s."""
    last_error = None
    for _ in range(3):
        try:
            return client.chat.completions.create(
                model=model, messages=messages, tools=tools, tool_choice="auto"
            )
        except BadRequestError as e:
            last_error = e
            if (e.body or {}).get("error", {}).get("code") != "tool_use_failed":
                raise
    raise last_error


def run_tool(tool_call):
    """Execute one tool call, always returning a dict for the model."""
    name = tool_call.function.name
    executor = get_executor(name)
    if executor is None:
        return tool_call.id, {"success": False, "error": f"Unknown tool: '{name}'"}

    try:
        args = json.loads(tool_call.function.arguments or "{}")
        return tool_call.id, {"success": True, "data": executor(**args)}
    except json.JSONDecodeError:
        return tool_call.id, {"success": False, "error": "Malformed JSON arguments."}
    except TypeError as e:
        return tool_call.id, {"success": False, "error": f"Invalid arguments for '{name}': {e}"}
    except ValueError as e:
        return tool_call.id, {"success": False, "error": str(e)}
    except Exception as e:
        return tool_call.id, {"success": False, "error": f"'{name}' failed: {type(e).__name__}"}


def run_agent_loop(client, model, messages, tools, verbose=True):
    """Loop until the model answers in text or MAX_TURNS is hit."""
    for _ in range(MAX_TURNS):
        msg = _create_completion(client, model, messages, tools).choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            return msg.content

        if verbose:
            print(f"  [tool calls: {', '.join(tc.function.name for tc in msg.tool_calls)}]")

        # Run parallel tool calls concurrently, then feed results back by id.
        with ThreadPoolExecutor(max_workers=len(msg.tool_calls)) as pool:
            results = dict(pool.map(run_tool, msg.tool_calls))

        for tc in msg.tool_calls:
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(results[tc.id]),
            })

    return "Sorry, I couldn't finish that within the allowed number of steps."
