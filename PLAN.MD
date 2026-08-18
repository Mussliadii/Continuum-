# PLAN.MD — Continuum: Never-Down SRE/Incident Copilot

## 1. Project Summary

An AI copilot for on-call SREs that helps diagnose production incidents by recalling semantically similar past incidents and their resolutions, while giving the agent — and the responder — real-time visibility into the health of its own memory layer (CockroachDB). The demo's centerpiece: simulate a CockroachDB node failure mid-incident and show the agent's memory keeps working without interruption.

**Team:** Solo
**Timeline:** 1–2 weeks
**Budget:** $0 target (see §5 Cost Tracking)

---

## 2. Requirements Checklist (mapped to official rules)

From [Des.md](Des.md) / [Resource.md](Resource.md):

- [x] Use **≥2 CockroachDB tools** → **Distributed Vector Indexing** + **Managed MCP Server**, both live and verified (ccloud CLI used for provisioning/ops as a 3rd)
- [x] Use **≥1 AWS service** → **AWS Lambda** + **Amazon API Gateway**, deployed and verified end-to-end against the real endpoint. (Amazon S3 was in the original plan as optional artifact storage but was never actually wired up — dropped from the writeup rather than claimed unused)
- [x] LICENSE (MIT) present at repo root
- [ ] Repo pushed to GitHub, public, LICENSE visible in About section — **your action**: I haven't pushed (you asked me to hold until you approve)
- [x] README with setup/run instructions
- [x] Public functional demo app URL → **https://continuum-beta-umber.vercel.app/** (verified: page loads, `NEXT_PUBLIC_API_BASE_URL` correctly baked into the production JS bundle, CORS from this exact origin to the Lambda API confirmed)
- [ ] Demo video <3 min — **your action**, needs a screen recorder/mic I don't have access to
- [x] Written explanation: which CockroachDB tools used + how (README)
- [x] Written explanation: which AWS services used + how (README)
- [x] Architecture diagram (Mermaid, in README)
- [ ] Optional: feedback for CockroachDB team

---

## 3. Architecture

```
┌────────────┐      HTTPS       ┌──────────────┐      invoke      ┌─────────────┐
│  Frontend  │ ───────────────► │ API Gateway  │ ───────────────► │   Lambda    │
│  (Vercel)  │ ◄─────────────── │              │ ◄─────────────── │ agent logic │
└────────────┘                  └──────────────┘                  └──────┬──────┘
   React/Next.js — DESIGN.MD layout                                       │
                                                                            │ tool calls
                        ┌───────────────────────────────────────────────┬─┴──────────────┐
                        ▼                                               ▼                 ▼
              ┌───────────────────┐                          ┌──────────────┐   ┌────────────────┐
              │   CockroachDB      │                          │  Groq API    │   │  Gemini API     │
              │   Cloud (Serverless)│                         │  (reasoning) │   │  (embeddings)   │
              │  - incidents table  │                         └──────────────┘   └────────────────┘
              │    + vector index   │
              │  - active_incidents │◄──── Managed MCP Server (cluster introspection: node
              │    (transactional)  │      health, latency, replica status) — called as an
              │  - MCP endpoint     │      agent tool during reasoning
              └──────────┬──────────┘
                         │
                         ▼
              ccloud CLI — used for cluster provisioning/ops automation
              (Serverless tier does not expose node-level failure control;
              see §7 Day 9 for how the resilience demo is actually staged)
```

**Data flow per chat turn:**
1. User message → API Gateway → Lambda.
2. Lambda embeds the message (Gemini embeddings) → vector search against `incidents` in CockroachDB → top-k similar incidents.
3. Lambda optionally calls the CockroachDB MCP Server tool to fetch live cluster health.
4. Lambda sends context (message + retrieved incidents + cluster state) to Groq (LLM) for reasoning → response.
5. Lambda writes the turn + any new hypothesis/action to `active_incidents` (transactional, CockroachDB) so state survives reload/restart.
6. On incident resolution, the summary is embedded and inserted into `incidents` — memory grows from use.

---

## 4. Tech Stack (final, all $0)

| Layer | Choice | Why |
|---|---|---|
| Database / memory | CockroachDB Cloud (Serverless, free tier) | Vector store + transactional store + MCP, no card needed |
| LLM reasoning | Groq API (Llama 3.3 70B) | Free, no card, fast, tool-calling support |
| Embeddings | Gemini API (text-embedding) | Free, no card, no expiry |
| Agent execution | AWS Lambda (Python 3.12) | Free tier 1M req/month forever; satisfies AWS requirement |
| API layer | Amazon API Gateway | Free tier; public HTTPS endpoint for Lambda |
| Artifact storage (optional) | Amazon S3 | Free tier 5GB/12mo, for raw postmortem docs |
| Frontend | Next.js on Vercel | Free forever, no card, instant public URL |
| Frontend styling | Tailwind CSS + design tokens from [DESIGN.MD](DESIGN.MD) | Matches design system directly |
| Icons | Phosphor Icons (`@phosphor-icons/react`) | Per DESIGN.MD |
| Fonts | Fira Code + Fira Sans (Google Fonts) | Per DESIGN.MD |
| DB client | `psycopg2` / `postgres` (node) or SQLAlchemy | CockroachDB is Postgres wire-compatible |
| Orchestration (optional) | LangChain (CockroachDB provider + Vector Store) | Official integration, saves boilerplate |

---

## 5. Cost Tracking (target: $0)

| Item | Expected cost | Safeguard |
|---|---|---|
| CockroachDB Cloud Serverless | $0 | Free tier, no card |
| Groq API | $0 | Free tier, no card |
| Gemini API | $0 | Free tier, no card, no expiry |
| AWS Lambda + API Gateway + S3 | $0 (within free tier) | **Set AWS Billing Alarm at $1** on day 1 |
| Vercel | $0 | Free tier, no card |
| **Total** | **$0** | — |

AWS account creation requires a card on file for identity verification (unavoidable, AWS-wide policy) — this is separate from actually being charged. Staying inside Lambda/API Gateway/S3 free-tier limits (far above hackathon demo scale) keeps actual spend at $0.

---

## 6. Database Schema (initial draft)

```sql
CREATE TABLE incidents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title STRING NOT NULL,
  description STRING NOT NULL,
  root_cause STRING,
  resolution STRING,
  severity STRING, -- 'critical' | 'warning' | 'info'
  tags STRING[],
  embedding VECTOR(768), -- Gemini embedding dimension
  created_at TIMESTAMPTZ DEFAULT now(),
  resolved_at TIMESTAMPTZ
);
CREATE VECTOR INDEX ON incidents (embedding);

CREATE TABLE active_incidents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title STRING NOT NULL,
  status STRING NOT NULL, -- 'investigating' | 'mitigating' | 'resolved'
  severity STRING NOT NULL,
  opened_at TIMESTAMPTZ DEFAULT now(),
  closed_at TIMESTAMPTZ
);

CREATE TABLE incident_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  incident_id UUID REFERENCES active_incidents(id),
  actor STRING NOT NULL, -- 'agent' | 'user'
  event_type STRING NOT NULL, -- 'message' | 'hypothesis' | 'action' | 'citation'
  content STRING NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

*(Refine once LangChain's CockroachDB Vector Store / Chat Message History schema conventions are reviewed — may adopt their table shape instead of a fully custom one to save time.)*

---

## 7. Day-by-Day Plan (10–12 working days)

### Week 1 — Foundation & Backend

- **Day 1 (today):** ✅ Strategy locked, DESIGN.MD + PLAN.MD written. Create CockroachDB Cloud cluster (free tier), AWS account + Billing Alarm ($1), Groq API key, Gemini API key, GitHub repo (MIT license), Vercel account.
- **Day 2:** ✅ Done. Schema implemented and applied to the live cluster (`scripts/apply_schema.py`), `CREATE VECTOR INDEX` + cosine similarity query verified end-to-end with test data (cleaned up after).
- **Day 3:** ✅ Done. 18 synthetic-but-realistic incidents seeded via `scripts/seed_incidents.py`, embedded with Gemini (`gemini-embedding-001`, 768 dims). Semantic search verified with a real query — correctly ranked "connection pool exhaustion" as the top match for a symptom description about slow DB-bound API responses. (Bug found + fixed: the Gemini `embedContent` REST response uses a singular `embedding.values` field, not the plural `embeddings[0].values` shape the docs implied — see `backend/src/embeddings.py`.)
- **Day 4:** ✅ Done. Agent core built (`backend/src/agent.py`): Groq (`openai/gpt-oss-120b`, migrated from the now-deprecated `llama-3.3-70b-versatile`) tool-calling loop over `search_similar_incidents` and transactional logging via `backend/src/incidents.py`. Tested locally end-to-end.
- **Day 5:** ✅ Done. `get_cluster_health` wired in via `backend/src/mcp_tool.py` (official `mcp` SDK, streamable HTTP transport, service-account bearer auth). Bugs found + fixed during testing:
  1. `mcp` SDK 2.0.0 renamed `streamablehttp_client` → `streamable_http_client`, changed its return arity (2 values, not 3), and renamed `Tool.inputSchema` → `Tool.input_schema`.
  2. The MCP client's TLS verification was flaky on this Windows dev box (intermittent `CERTIFICATE_VERIFY_FAILED`) — pinned `certifi`'s CA bundle instead of relying on the OS trust store, same fix as the earlier CockroachDB SQL connection issue.
  3. Serverless clusters report `node_count: 0` for every region (node topology is abstracted away by design) — the agent initially misread this as "cluster is down." Fixed by adding an explicit clarifying note in the tool's return payload; verified the agent now correctly reports the DB as healthy.
  4. `get_cluster_health()` called `asyncio.run()` unconditionally, which crashes with "cannot be called from a running event loop" once invoked from inside FastAPI/uvicorn (or anything else that already has a loop running). Fixed by detecting a running loop and, if present, executing the coroutine in a dedicated thread instead. Verified against both a plain script (no loop) and the local FastAPI dev server (loop already running).
  5. `backend/src/db.py` originally called `load_dotenv()` itself, which would have pulled `python-dotenv` into the Lambda deployment package unnecessarily and blurred the line between local-dev and runtime config. Moved `load_dotenv()` calls to each local-only entry point (`scripts/*.py`, `backend/src/local_server.py`) and split `backend/requirements-dev.txt` (local-only: `python-dotenv`, `fastapi`, `uvicorn`) from `backend/requirements.txt` (Lambda runtime deps only).

  Built and verified end-to-end over real HTTP (not just direct function calls) against a local FastAPI dev server (`backend/src/local_server.py`, mirrors the exact Lambda routing in `backend/src/handler.py`): `POST /chat`, `GET /incidents/{id}` (reload/persistence), `POST /incidents/{id}/resolve` (closes the self-improving-memory loop — confirmed a resolved incident is embedded and appended to the knowledge base). Added `scripts/reset_demo_data.py` to restore a clean 18-incident seed state before recording the submission video.
- **Day 6:** ✅ Done. Deployed to a real AWS account using a scoped-down IAM user (`AWSLambda_FullAccess` + `AmazonAPIGatewayAdministrator` + an inline policy limited to creating/passing exactly one role, `continuum-lambda-role` — no admin/root access). Live endpoint verified end-to-end: `https://x7452bjwt9.execute-api.ap-southeast-3.amazonaws.com` (region matches the CockroachDB cluster's `ap-southeast-3`). Bugs found + fixed along the way:
  1. Developing on Windows but deploying to Lambda (Amazon Linux x86_64) meant a plain local `pip install` would have bundled Windows-native binaries for `psycopg2-binary` etc. Solved with `pip install --platform manylinux2014_x86_64 --python-version 3.12 ...` (no Docker/AWS CLI needed) in `scripts/build_lambda_package.py`.
  2. Unpinned `mcp` in requirements.txt let pip silently backtrack to `mcp==1.10.1` (a different, incompatible API) while resolving the cross-platform install — would have crashed at runtime with no local warning. Root cause, and the actual fix: `mcp`'s `pywin32` Windows-only dependency marker is evaluated against the *host* OS (Windows) regardless of the `--platform` target, so it can never resolve cleanly when building for Lambda from Windows. Replaced the official `mcp` SDK entirely with a ~60-line JSON-RPC-over-`requests` client in `backend/src/mcp_tool.py` — smaller, no async/threading workaround needed, and sidesteps the packaging issue completely. (Confirmed via direct curl testing that CockroachDB's MCP server is stateless per-request — no `initialize` handshake or session ID required — which is what made this simplification possible.)
  3. Simplified `handler.py` to parse path parameters from `rawPath` via regex instead of relying on API Gateway's `pathParameters`, so deployment could use a single "quick create" HTTP API (`Target=<lambda_arn>` in one boto3 call — auto-wires the integration, `$default` route, and Lambda invoke permission) instead of hand-building per-route resources.

  Tooling added: `scripts/build_lambda_package.py` (packaging), `scripts/deploy_lambda.py` (boto3-based create/update of the IAM role, Lambda function, and HTTP API — idempotent, safe to rerun for future updates).

### Week 2 — Frontend, Resilience Demo, Submission

- **Day 7 + 8 (combined):** ✅ Done. Next.js 16 (App Router, Turbopack, Tailwind v4) scaffolded in `frontend/`, implementing the full DESIGN.MD app shell: `TopBar` (live cluster-health pulse), `LeftRail`, `ChatPanel` (empty state, citation-chip parsing linking `[INC-xxx]` references to the matching card, loading/disabled composer state), `RightRail` (stacked panels on desktop, tabbed on mobile/tablet — `SimilarIncidentsPanel`, `ClusterHealthPanel`, `TimelinePanel`), `ResolveModal`. Design tokens ported to Tailwind v4 `@theme`; Fira Code/Fira Sans via `next/font/google` (self-hosted, not the manual `<link>` import from DESIGN.MD, which is the more idiomatic Next.js approach). Wired directly to the real deployed Lambda API via `NEXT_PUBLIC_API_BASE_URL`.

  Verified: `tsc --noEmit` clean, `eslint` clean, `next build` succeeds, dev server SSR output inspected via curl (correct structure: top bar, nav, empty-state copy, all three right-rail panels present), and a live CORS preflight against the deployed API from a `localhost:3000` origin returns the expected `access-control-allow-*` headers. **Not verified: actual visual appearance or interactive behavior in a real browser** — no browser/screenshot tool is available in this environment. The build/type/lint/render checks catch structural and logic errors but not visual polish, layout bugs, or runtime UI glitches; a real browser pass (by you, or a future session with that tooling) is still needed before considering Day 7-8 fully closed.

  One bug found + fixed: `HexagonDashed` doesn't exist in `@phosphor-icons/react` — corrected to `Hexagon` after checking the package's actual type declarations rather than guessing.
- **Day 9:** ✅ Prepared, ⚠️ **not yet run — needs your confirmation it works.** This dev environment has no Docker and no WSL Linux distro installed (confirmed: `docker`/`cockroach` commands not found, `wsl -l -v` shows zero distros), and installing a WSL distro is a real system change I won't do without explicit sign-off. Since you asked for a zero-desktop-install alternative, built the demo around **GitHub Codespaces** instead (60 free hours/month on a personal GitHub account, Docker included, runs entirely in-browser):
  - `.devcontainer/devcontainer.json` — Codespace config with Docker-in-Docker
  - `resilience-demo/docker-compose.yml` — 3-node insecure CockroachDB cluster, pinned to v26.2.5 to match the Cloud cluster's version, following the [official Docker multi-node pattern](https://www.cockroachlabs.com/docs/v26.2/start-a-local-cluster-in-docker-mac)
  - `resilience-demo/workload.py` — round-robins queries across all 3 nodes' SQL ports once per second so a killed node's own endpoint failing (expected) is visually distinct from the surviving nodes continuing to serve the same data (the actual resilience proof)
  - `resilience-demo/README.md` — exact steps to open a Codespace, start the cluster, run the workload, kill/restart a node, and what to narrate in the video

  **I could not execute or verify any of this myself** — no Codespaces/Docker access in this session. It's built directly from official CockroachDB Docker docs, but you need to actually run through `resilience-demo/README.md` yourself before recording, in case something needs adjusting.
- **Day 10:** Partial — did a code-level pass against DESIGN.MD §5 (I have no browser here, so this is static-analysis, not a real device/viewport check). Found and fixed two real bugs:
  1. Send button and the resolve-modal close button were 42px/18px hit areas, under the 44×44px minimum the design doc itself specifies — resized to 44×44px (`h-11 w-11`).
  2. The "jump to similarity card" highlight on citation click used the CSS `:target` pseudo-class, which only fires for URL-fragment navigation — but the click handler calls `.focus()` programmatically, so the highlight could never have appeared. Fixed to `:focus`.

  **Still outstanding, needs a real browser:** actual responsive behavior at 375/768/1024/1440px, visual contrast as rendered (not just token values), hover/focus states as they actually look, and general "does this feel right" polish. Flagging clearly rather than claiming this is done.
- **Day 11:** Partial — ✅ README rewritten with a full architecture diagram (Mermaid, renders natively on GitHub), CockroachDB-tools-used and AWS-services-used writeups (each pointing at the specific file/function that uses it), and complete setup/run instructions. ⏳ **Video recording, and the repo's actual GitHub push, are yours to do** — I can't operate a screen recorder, a microphone, or your GitHub login from here.
- **Day 12 (buffer):** Not started — see the checklist below for exactly what's left and who does it.

---

## 8. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Empty vector search looks unimpressive in demo | Day 3 seed dataset is non-negotiable — do it early, not last-minute |
| Resilience demo needs a literal node kill, which Serverless doesn't expose | **Resolved:** confirmed Serverless has no node-failure control (Advanced-tier-only Cloud Console feature). Plan now uses CockroachDB's documented local multi-node resilience demo instead — verify this runs cleanly on the dev machine by Day 3, not Day 9 |
| Groq/Gemini free-tier rate limits hit during demo recording | Both tiers are generous (30 req/min Groq, 15 RPM Gemini) — fine for a scripted <3min demo, just don't hammer it during dev in the same minute as recording |
| AWS Lambda cold starts make demo feel slow | Add a loading state (per DESIGN.MD) so it reads as "agent thinking," not broken |
| Scope creep (Knowledge Base page, Settings page, auth) | Left-rail nav items beyond Chat/History can be visual-only placeholders for the demo — don't build full CRUD for features judges won't click into during a 3-min video |
| Time runs out before video/README polish | Days 11–12 are protected — if behind schedule, cut Day 10 polish before cutting submission materials |

---

## 9. Open Questions

1. ~~Does CockroachDB Cloud Serverless free tier allow triggering/observing a node failure?~~ **RESOLVED (verified via official docs):** No — node-level fault injection ("Fault Tolerance Demo") is an Advanced-tier-only Cloud Console feature requiring a ≥3-node dedicated cluster. Serverless (our tier) hides node topology entirely. **Decision:** stage the resilience segment using CockroachDB's own [documented local multi-node resilience demo](https://www.cockroachlabs.com/docs/stable/demo-cockroachdb-resilience) instead (kill a node process on a local open-source cluster, show self-healing) — same underlying mechanism, officially sanctioned demo pattern, zero cost. Video/README must frame this honestly as a technical demonstration, not footage of our actual production Serverless cluster.
2. ~~Exact vector column type/dimension support on current CockroachDB version?~~ **RESOLVED (verified live on v26.2.5 cluster):** `VECTOR(768)` column type works; vector indexes require `SET CLUSTER SETTING feature.vector_index.enabled = true` first (not on by default); `CREATE VECTOR INDEX ... ON table (embedding vector_cosine_ops)` and the `<=>` cosine-distance operator both confirmed working end-to-end with a live insert + similarity query against the real cluster. Schema applied via `scripts/apply_schema.py`.
3. ~~Is the Managed MCP Server reachable server-to-server from Lambda?~~ **RESOLVED (verified via official docs):** Yes — the Managed MCP Server explicitly supports **service account API keys** for "fully autonomous agent pipelines," separate from the OAuth 2.1 flow used by interactive tools like Claude Code/Cursor. Every call is still Cloud-RBAC-checked and audited. Lambda can call it directly using a service account key in the Authorization header — no interactive/browser auth required. Architecture in §3 stands as designed.

---

## 10. Final Status — What's Built vs. What's Left

**Fully built, tested, and verified end-to-end against real services** (not mocked): database schema + vector search, the Groq tool-calling agent, the MCP cluster-health tool, transactional incident state + the self-improving-memory loop, Lambda + API Gateway deployment, and the Next.js frontend (build/lint/type-check clean, structural SSR render checked, CORS to the live API confirmed).

**What I could not do myself, and why** — all of these need you:
- **See the UI in an actual browser.** No browser/screenshot tool is available in this session. Everything in Day 7-8-10 was verified by build tooling and reading rendered HTML, not by looking at it. Please open `npm run dev` in a real browser before recording anything.
- **Run the resilience demo.** No Docker, no WSL distro, and installing one is a system change I won't make without your sign-off. Built for GitHub Codespaces instead (zero desktop install) per your request — see `resilience-demo/README.md` — but never executed it myself.
- **Push to GitHub, deploy the frontend to Vercel, record the video, fill out and submit the Devpost form.** All explicitly outside what I can do from here (your GitHub/Vercel logins, a screen recorder, a form only you can submit).

**Suggested order for your remaining pass:**
1. `git add`, commit, push to GitHub (ask me if you want help drafting the commit).
2. Open the app in a real browser (`npm run dev` in `frontend/`) and fix anything that looks wrong — tell me and I'll patch it.
3. Deploy `frontend/` to Vercel, update the README/submission with the live URL.
4. Walk through `resilience-demo/README.md` once, before recording, to confirm it actually works.
5. Run `scripts/reset_demo_data.py` for a clean seed state, then record the video.
6. Submit on Devpost.
