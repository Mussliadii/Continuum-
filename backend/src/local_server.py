"""Local development server.

Wraps the exact same `lambda_handler` used in production behind a single
catch-all route — mirroring the "quick create" HTTP API's $default route
used in deployment (see scripts/deploy_lambda.py) — so local behavior
matches the deployed Lambda exactly. All routing logic lives in
handler.py; this file only translates a Starlette request into an API
Gateway HTTP API (payload format 2.0) event.

Run with: uvicorn local_server:app --reload --port 8000
"""

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.responses import Response  # noqa: E402

from handler import lambda_handler  # noqa: E402

app = FastAPI(title="Continuum backend (local)")


@app.api_route("/{full_path:path}", methods=["GET", "POST", "OPTIONS"])
async def catch_all(full_path: str, request: Request):
    body = await request.body()
    event = {
        "requestContext": {"http": {"method": request.method}},
        "rawPath": f"/{full_path}",
        "body": body.decode("utf-8") if body else None,
    }
    result = lambda_handler(event, None)
    return Response(
        content=result.get("body", ""),
        status_code=result["statusCode"],
        media_type="application/json",
    )
