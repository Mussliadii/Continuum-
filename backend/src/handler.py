"""AWS Lambda entry point, invoked via API Gateway (HTTP API, payload format 2.0).

Routes:
    POST /chat                       {message, incident_id?} -> agent turn
    GET  /incidents/{incident_id}    -> active incident + full event timeline
    POST /incidents/{incident_id}/resolve  {description, root_cause, resolution, tags}

CORS is handled here directly (no API Gateway CORS config needed) so the
Vercel-hosted frontend, on a different origin, can call this API.

Path parameters are parsed from `rawPath` with a plain regex rather than
relying on API Gateway's `pathParameters`, which requires explicitly
configured `{param}` routes. This lets the API Gateway side stay a single
catch-all "quick create" HTTP API (one boto3 call, auto-wired integration
and Lambda permission) instead of hand-built per-route resources — and it
means the exact same event shape works against the local FastAPI dev
server (see local_server.py), which naturally sets `rawPath` to the real
request path.
"""

import json
import re

from agent import run_agent_turn
from incidents import get_active_incident, get_incident_events, resolve_incident

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", **CORS_HEADERS},
        "body": json.dumps(body, default=str),
    }


def _handle_chat(body: dict) -> dict:
    message = body.get("message")
    if not message:
        return _response(400, {"error": "message is required"})
    result = run_agent_turn(message, incident_id=body.get("incident_id"))
    return _response(200, result)


def _handle_get_incident(incident_id: str) -> dict:
    incident = get_active_incident(incident_id)
    if incident is None:
        return _response(404, {"error": "incident not found"})
    events = get_incident_events(incident_id)
    return _response(200, {"incident": incident, "events": events})


def _handle_resolve_incident(incident_id: str, body: dict) -> dict:
    required = ["description", "root_cause", "resolution", "tags"]
    missing = [field for field in required if field not in body]
    if missing:
        return _response(400, {"error": f"missing fields: {missing}"})
    resolve_incident(
        incident_id,
        description=body["description"],
        root_cause=body["root_cause"],
        resolution=body["resolution"],
        tags=body["tags"],
    )
    return _response(200, {"status": "resolved"})


_RESOLVE_PATH = re.compile(r"^/incidents/([^/]+)/resolve$")
_INCIDENT_PATH = re.compile(r"^/incidents/([^/]+)$")


def lambda_handler(event: dict, _context) -> dict:
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = event.get("rawPath", "/")

    if method == "OPTIONS":
        return {"statusCode": 204, "headers": CORS_HEADERS, "body": ""}

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"error": "invalid JSON body"})

    try:
        if method == "POST" and path == "/chat":
            return _handle_chat(body)

        if method == "POST" and (m := _RESOLVE_PATH.match(path)):
            return _handle_resolve_incident(m.group(1), body)

        if method == "GET" and (m := _INCIDENT_PATH.match(path)):
            return _handle_get_incident(m.group(1))

        return _response(404, {"error": f"no route for {method} {path}"})
    except Exception as exc:  # noqa: BLE001 — surface as a 500 rather than a cold Lambda crash
        return _response(500, {"error": str(exc)})
