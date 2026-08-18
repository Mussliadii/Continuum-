"""Agent orchestration: a Groq tool-calling loop over two tools backed by
CockroachDB — semantic search (Distributed Vector Indexing) and live
cluster introspection (Managed MCP Server) — plus transactional logging of
every turn so the incident's state survives a reload or cold start.
"""

import json
import os

from groq import Groq

from incidents import create_incident, get_incident_events, log_event
from mcp_tool import get_cluster_health
from vector_search import search_similar_incidents

MODEL = "openai/gpt-oss-120b"
MAX_TOOL_ITERATIONS = 4

SYSTEM_PROMPT = """You are Continuum, an on-call SRE's incident copilot.

You help diagnose production incidents by recalling similar past incidents \
and their resolutions, and by checking the live health of the CockroachDB \
cluster that stores your own memory when the incident looks database-related.

Tools:
- search_similar_incidents: search the incident knowledge base by symptom description.
- get_cluster_health: check the live state of your own memory layer's database cluster.

When you cite a past incident, reference it inline like [INC-<short_id>] using the \
short_id field from the search results, so the responder can trace your reasoning \
back to evidence. Be concise and concrete: lead with the most likely cause, cite the \
evidence, then suggest a next action.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_similar_incidents",
            "description": (
                "Search the incident knowledge base for past incidents semantically "
                "similar to a description of current symptoms. Returns title, "
                "severity, root cause, resolution, and similarity distance "
                "(lower distance = more similar)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A description of the current symptoms or situation.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max number of results to return.",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cluster_health",
            "description": (
                "Get the live health of the CockroachDB cluster that powers this "
                "agent's own memory: state, region, version, and currently running "
                "queries. Use this when the incident might be database-related, or "
                "when asked about the memory layer's own status."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

TOOL_IMPLEMENTATIONS = {
    "search_similar_incidents": lambda args: search_similar_incidents(
        args["query"], args.get("limit", 5)
    ),
    "get_cluster_health": lambda _args: get_cluster_health(),
}


def _event_to_message(event: dict) -> dict:
    role = "assistant" if event["actor"] == "agent" else "user"
    return {"role": role, "content": event["content"]}


def run_agent_turn(user_message: str, incident_id: str | None = None) -> dict:
    """Process one chat turn. Creates a new active incident if none is given.

    Returns: {incident_id, response, similar_incidents, cluster_health}
    """
    if incident_id is None:
        title = user_message[:80]
        incident_id = create_incident(title)
        history = []
    else:
        history = [_event_to_message(e) for e in get_incident_events(incident_id)]

    log_event(incident_id, "user", "message", user_message)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history, {"role": "user", "content": user_message}]

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    similar_incidents: list[dict] = []
    cluster_health: dict | None = None

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS, tool_choice="auto"
        )
        message = response.choices[0].message

        if not message.tool_calls:
            final_text = message.content or ""
            log_event(incident_id, "agent", "message", final_text)
            return {
                "incident_id": incident_id,
                "response": final_text,
                "similar_incidents": similar_incidents,
                "cluster_health": cluster_health,
            }

        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [tc.model_dump() for tc in message.tool_calls],
            }
        )

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments or "{}")
            try:
                result = TOOL_IMPLEMENTATIONS[name](args)
            except Exception as exc:  # noqa: BLE001 — tool failures are reported to the model, not raised
                result = {"error": str(exc)}

            if name == "search_similar_incidents" and isinstance(result, list):
                similar_incidents = result
                for hit in result:
                    log_event(
                        incident_id,
                        "agent",
                        "citation",
                        f"[INC-{hit['short_id']}] {hit['title']} (distance={hit['distance']:.3f})",
                    )
            elif name == "get_cluster_health" and isinstance(result, dict):
                cluster_health = result

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )

    # Safety net: stop looping and surface whatever the model has said so far.
    fallback_text = "I gathered some context but couldn't finish reasoning in time — could you rephrase or narrow the question?"
    log_event(incident_id, "agent", "message", fallback_text)
    return {
        "incident_id": incident_id,
        "response": fallback_text,
        "similar_incidents": similar_incidents,
        "cluster_health": cluster_health,
    }
