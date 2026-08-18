"""Client for CockroachDB's Managed MCP Server.

Authenticates with a service-account API key (server-to-server, no
interactive OAuth) as documented at:
https://www.cockroachlabs.com/docs/cockroachcloud/connect-to-the-cockroachdb-cloud-mcp-server

This talks JSON-RPC directly over `requests` rather than pulling in the
official `mcp` SDK. That SDK is built for running a full client/server
session (it ships FastAPI/Starlette/uvicorn/sse-starlette on the wire
whether or not you need them) and — more concretely — its Windows-only
`pywin32` dependency marker breaks cross-platform packaging for AWS Lambda
(pip evaluates `sys_platform` against the *host* running pip, not the
`--platform` target, so building on Windows for Lambda's Linux runtime
fails outright). A live check against the endpoint confirmed each JSON-RPC
call is independently authenticated and stateless — no `initialize`
handshake or session ID is required before `tools/call` — so a minimal
client is both simpler and more reliable than the full SDK for this use case.
"""

import json
import os

import certifi
import requests


def _call_tool(tool_name: str, arguments: dict) -> dict:
    endpoint = os.environ["COCKROACHDB_MCP_ENDPOINT"]
    api_key = os.environ["COCKROACHDB_MCP_SERVICE_ACCOUNT_KEY"]

    response = requests.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        },
        timeout=30,
        verify=certifi.where(),
    )
    response.raise_for_status()

    # Response body is a single SSE event, e.g. "event: message\ndata: {...}\n"
    data_line = next(line for line in response.text.splitlines() if line.startswith("data:"))
    payload = json.loads(data_line[len("data:"):].strip())

    if "error" in payload:
        raise RuntimeError(f"MCP tool '{tool_name}' failed: {payload['error']}")

    content_blocks = payload["result"]["content"]
    text = "".join(block.get("text", "") for block in content_blocks)
    return json.loads(text)


def _resolve_cluster_id() -> str:
    clusters = _call_tool("list_clusters", {})
    return clusters["rows"][0]["id"]


def get_cluster_health() -> dict:
    """Live health of the CockroachDB cluster backing this agent's memory."""
    cluster_id = _resolve_cluster_id()
    cluster = _call_tool("get_cluster", {"cluster_id": cluster_id})
    running_queries = _call_tool("show_running_queries", {"cluster_id": cluster_id})
    return {
        "cluster_name": cluster.get("name"),
        "state": cluster.get("state"),
        "cockroach_version": cluster.get("cockroach_version"),
        "regions": [r.get("name") for r in cluster.get("regions", [])],
        "active_query_count": len(running_queries.get("rows", [])),
        "note": (
            "This is a Serverless cluster: per-node topology is abstracted away by "
            "design (CockroachDB manages node distribution transparently), so there "
            "is no meaningful per-node count to report here. Judge health from "
            "'state' (e.g. CREATED/READY = healthy) and 'active_query_count', not "
            "from node counts."
        ),
    }
