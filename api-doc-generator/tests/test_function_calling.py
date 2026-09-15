"""Tests for function calling / tools pattern and change explanation service."""

import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace
from sqlmodel import Session

from app.services.llm_client import call_with_tools
from app.services.change_explanation_service import ChangeExplanationService, EXPLANATION_TOOLS


class TestCallWithTools:
    def test_returns_tool_call(self):
        mock_client = MagicMock()

        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "explain_breaking_change"
        mock_tool_call.function.arguments = '{"impact": "Clients will fail", "migration_steps": "Update calls", "risk_level": "high"}'

        mock_message = MagicMock()
        mock_message.tool_calls = [mock_tool_call]

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]

        mock_client.chat.completions.create.return_value = mock_completion

        result = call_with_tools(
            client=mock_client,
            system_prompt="Test",
            user_prompt="Test change",
            tools=EXPLANATION_TOOLS,
        )

        assert result is not None
        assert result["name"] == "explain_breaking_change"
        assert result["arguments"]["impact"] == "Clients will fail"
        assert result["arguments"]["risk_level"] == "high"

    def test_returns_none_when_no_tool_called(self):
        mock_client = MagicMock()

        mock_message = MagicMock()
        mock_message.tool_calls = None

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]

        mock_client.chat.completions.create.return_value = mock_completion

        result = call_with_tools(
            client=mock_client,
            system_prompt="Test",
            user_prompt="Test",
            tools=EXPLANATION_TOOLS,
        )

        assert result is None

    def test_tools_passed_to_api(self):
        mock_client = MagicMock()

        mock_message = MagicMock()
        mock_message.tool_calls = None
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_completion

        call_with_tools(
            client=mock_client,
            system_prompt="Test",
            user_prompt="Test",
            tools=EXPLANATION_TOOLS,
        )

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["tools"] == EXPLANATION_TOOLS
        assert call_kwargs["tool_choice"] == "auto"


class TestChangeExplanationService:
    @patch("app.services.change_explanation_service.call_with_tools")
    def test_explain_breaking_change(self, mock_call, session):
        from app.models.project import Project
        from app.models.api_version import APIVersion
        from app.models.endpoint import Endpoint

        project = Project(name="Test")
        session.add(project)
        session.commit()
        session.refresh(project)

        v1 = APIVersion(project_id=project.id, version="1.0.0")
        v2 = APIVersion(project_id=project.id, version="1.1.0")
        session.add(v1)
        session.add(v2)
        session.commit()
        session.refresh(v1)
        session.refresh(v2)

        # v1 has endpoint, v2 doesn't → removed → breaking
        ep = Endpoint(
            project_id=project.id, version_id=v1.id,
            path="/users", method="GET",
        )
        session.add(ep)
        session.commit()

        mock_call.return_value = {
            "name": "explain_breaking_change",
            "arguments": {
                "impact": "Clients calling GET /users will get 404.",
                "migration_steps": "Remove all calls to GET /users.",
                "risk_level": "high",
            },
        }

        service = ChangeExplanationService(session)
        results = service.explain_changes(project.id, v1.id, v2.id)

        assert len(results) >= 1

        breaking = [r for r in results if r["explanation"]["tool_used"] == "explain_breaking_change"]
        assert len(breaking) >= 1
        assert "impact" in breaking[0]["explanation"]
        assert "migration_steps" in breaking[0]["explanation"]
