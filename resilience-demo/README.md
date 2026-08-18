# Resilience Demo (no desktop install required)

This demonstrates the resilience mechanism that makes CockroachDB suited as
an agent's memory layer: a 3-node cluster keeps serving reads even after
one node is killed, then self-heals when it comes back.

**Why this exists separately from the deployed app:** the production app
runs on CockroachDB Cloud **Serverless**, which is fully managed and
abstracts node topology away — there's no way to kill a specific node on
that tier (that's an Advanced-tier-only feature; see PLAN.MD §9). This
local cluster runs the same CockroachDB version (v26.2.5) to demonstrate
the underlying mechanism directly. Say this plainly in the video — don't
imply the Cloud Serverless cluster itself was killed.

## Run it with zero installs, via GitHub Codespaces

1. Push this repo to GitHub (if not already).
2. On the repo page: **Code → Codespaces → Create codespace on main**.
   This opens a full Linux + Docker environment in your browser — nothing
   installs on your own machine. GitHub gives every free account 60
   hours/month of this at no cost.
3. Once the Codespace terminal is ready, run:
   ```bash
   cd resilience-demo
   docker compose up -d
   docker exec -it roach1 ./cockroach --host=roach1:26357 init --insecure
   ```
4. Open a **second terminal** in the same Codespace (there's a `+` in the
   terminal panel) and start the workload:
   ```bash
   cd resilience-demo
   pip install psycopg2-binary
   python3 workload.py
   ```
   You'll see one line per second, round-robining across all three nodes'
   SQL ports — this is what you record for the video.
5. In the **first terminal**, kill one node to simulate its failure:
   ```bash
   docker compose stop roach2
   ```
   Watch the workload output: `roach2`'s lines start failing (expected —
   that specific node is down), but `roach1` and `roach3` keep returning
   the same row successfully, **without interruption**. That's the
   point: the data survived because it's replicated, not because any one
   node is special.
6. Bring it back and show self-healing:
   ```bash
   docker compose start roach2
   ```
   Give it a few seconds — `roach2`'s lines in the workload output resume
   succeeding once it rejoins and catches up.
7. When done recording: `docker compose down -v` to clean up.

## What to narrate in the video

- "This is the same CockroachDB version as our production Serverless
  cluster, run locally to make the failure visible."
- Point out the moment `roach2` starts failing while `roach1`/`roach3`
  keep succeeding — that's the resilience guarantee in action.
- Point out `roach2` recovering on its own once restarted — no manual
  data recovery step.

## Alternative: Docker Desktop on your own machine

If you'd rather not use Codespaces, the exact same steps work locally
once Docker Desktop is installed — nothing else in this folder changes.
