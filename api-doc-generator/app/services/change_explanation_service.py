import json

from openai import OpenAI
from sqlmodel import Session

from app.services.llm_client import get_llm_client, call_with_tools
from app.services.version_comparison_service import VersionComparisonService


EXPLANATION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "explain_breaking_change",
            "description": "Explain why a breaking API change will impact existing clients and what they need to do.",
            "parameters": {
                "type": "object",
                "properties": {
                    "impact": {
                        "type": "string",
                        "description": "What will break for existing API clients.",
                    },
                    "migration_steps": {
                        "type": "string",
                        "description": "Step-by-step instructions for clients to migrate.",
                    },
                    "risk_level": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Risk level of this change.",
                    },
                },
                "required": ["impact", "migration_steps", "risk_level"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "explain_non_breaking_change",
            "description": "Explain a non-breaking or informational API change.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Brief summary of what changed and why it's safe.",
                    },
                    "benefits": {
                        "type": "string",
                        "description": "Benefits of this change for API consumers.",
                    },
                },
                "required": ["summary", "benefits"],
            },
        },
    },
]

SYSTEM_PROMPT = (
    "You are an API compatibility expert. "
    "Given a detected API change, use the appropriate tool to explain it. "
    "Use 'explain_breaking_change' for breaking changes. "
    "Use 'explain_non_breaking_change' for non-breaking or informational changes."
)


class ChangeExplanationService:

    def __init__(self, session: Session, client: OpenAI | None = None):
        self.comparison_service = VersionComparisonService(session)
        self.client = client or get_llm_client()

    def explain_changes(
        self,
        project_id: int,
        from_version_id: int,
        to_version_id: int,
    ) -> list[dict]:
        comparison = self.comparison_service.compare_versions(
            project_id, from_version_id, to_version_id,
        )

        explained_changes = []

        for change in comparison["changes"]:
            explanation = self._explain_change(change)

            explained_changes.append({
                "change": change.model_dump(),
                "explanation": explanation,
            })

        return explained_changes

    def _explain_change(self, change) -> dict:
        user_prompt = (
            f"API Change Detected:\n"
            f"  Type: {change.type}\n"
            f"  Severity: {change.severity}\n"
            f"  Message: {change.message}\n"
        )

        if change.method:
            user_prompt += f"  Endpoint: {change.method} {change.path}\n"
        if change.component:
            user_prompt += f"  Component: {change.component}\n"
        if change.field:
            user_prompt += f"  Field: {change.field}\n"
        if change.old_value is not None:
            user_prompt += f"  Old value: {change.old_value}\n"
        if change.new_value is not None:
            user_prompt += f"  New value: {change.new_value}\n"

        user_prompt += "\nExplain this change using the appropriate tool."

        result = call_with_tools(
            client=self.client,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            tools=EXPLANATION_TOOLS,
        )

        if result:
            return {
                "tool_used": result["name"],
                **result["arguments"],
            }

        return {
            "tool_used": "none",
            "summary": change.message,
        }
