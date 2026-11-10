"""Server-side tool selection applies to discovery and explicit calls."""

import asyncio
from unittest.mock import patch

import pytest

from codegraphcontext.server import MCPServer


def make_server(tmp_path):
    with patch("codegraphcontext.server.get_database_manager"), \
         patch("codegraphcontext.server.JobManager"), \
         patch("codegraphcontext.server.GraphBuilder"), \
         patch("codegraphcontext.server.CodeFinder"), \
         patch("codegraphcontext.server.CodeWatcher"):
        return MCPServer(cwd=tmp_path)


def test_allow_list_filters_discovery_and_calls(monkeypatch, tmp_path):
    monkeypatch.setenv("CGC_ENABLED_TOOLS", "find_code, get_graph_guide")
    server = make_server(tmp_path)
    assert set(server.tools) == {"find_code", "get_graph_guide"}
    result = asyncio.run(server.handle_tool_call("delete_repository", {"repo_path": "."}))
    assert "disabled" in result["error"]


@pytest.mark.parametrize("selection", ["find_cdoe", ", ,"])
def test_invalid_selection_fails_loudly(monkeypatch, tmp_path, selection):
    monkeypatch.setenv("CGC_ENABLED_TOOLS", selection)
    with pytest.raises(ValueError, match="CGC_ENABLED_TOOLS"):
        make_server(tmp_path)


def test_project_deny_list_takes_precedence(monkeypatch, tmp_path):
    monkeypatch.setenv("CGC_ENABLED_TOOLS", "find_code,get_graph_guide")
    (tmp_path / "mcp.json").write_text(
        '{"mcpServers":{"CodeGraphContext":{"tools":{"disabledTools":["find_code"]}}}}'
    )
    assert set(make_server(tmp_path).tools) == {"get_graph_guide"}
