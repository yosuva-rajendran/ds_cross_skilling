import json

from openai import OpenAI
from pydantic import BaseModel

from app.core.config import settings


def get_llm_client() -> OpenAI:
    kwargs = {"api_key": settings.openai_api_key}

    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url

    return OpenAI(**kwargs)


def generate_structured(
    client: OpenAI,
    system_prompt: str,
    user_prompt: str,
    response_model: type[BaseModel],
) -> BaseModel:
    schema = response_model.model_json_schema()

    full_system = (
        f"{system_prompt}\n\n"
        f"You MUST respond with valid JSON matching this exact schema:\n"
        f"{json.dumps(schema, indent=2)}\n\n"
        f"Return ONLY the JSON object. No markdown, no code fences, no extra text."
    )

    completion = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": full_system},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=1024,
    )

    raw_content = completion.choices[0].message.content.strip()

    if raw_content.startswith("```"):
        lines = raw_content.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw_content = "\n".join(lines)

    parsed = json.loads(raw_content)
    return response_model.model_validate(parsed)


def call_with_tools(
    client: OpenAI,
    system_prompt: str,
    user_prompt: str,
    tools: list[dict],
) -> dict | None:
    completion = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        tools=tools,
        tool_choice="auto",
        temperature=0.3,
        max_tokens=1024,
    )

    message = completion.choices[0].message

    if message.tool_calls:
        tool_call = message.tool_calls[0]
        return {
            "name": tool_call.function.name,
            "arguments": json.loads(tool_call.function.arguments),
        }

    return None
