# Resilience Demo

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

**Status: verified working end-to-end** (with Docker Desktop, Windows) —
see the sample run at the bottom of this file for exactly what to expect.

## Run it

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/).

1. From the repo root:
   ```bash
   cd resilience-demo
   docker compose up -d
   docker exec resilience-demo-roach1-1 ./cockroach --host=roach1:26357 init --insecure
   ```
2. In a **second terminal**, start the workload:
   ```bash
   cd resilience-demo
   pip install psycopg2-binary
   python workload.py
   ```
   You'll see one line per second, round-robining across all three nodes'
   SQL ports — this is what you record for the video.
3. In the **first terminal**, kill one node to simulate its failure:
   ```bash
   docker compose stop roach2
   ```
   Watch the workload output: `roach2`'s lines start failing (expected —
   that specific node is down), but `roach1` and `roach3` keep returning
   the same row successfully, **without interruption**. That's the
   point: the data survived because it's replicated, not because any one
   node is special.
4. Bring it back and show self-healing:
   ```bash
   docker compose start roach2
   ```
   `roach2`'s lines in the workload output resume succeeding within a
   few seconds of it rejoining and catching up.
5. When done recording: `docker compose down -v` to clean up.

## What to narrate in the video

- "This is the same CockroachDB version as our production Serverless
  cluster, run locally to make the failure visible."
- Point out the moment `roach2` starts failing while `roach1`/`roach3`
  keep succeeding — that's the resilience guarantee in action.
- Point out `roach2` recovering on its own once restarted — no manual
  data recovery step.

## Sample run (actual output from a verification pass)

```
[02:58:57] OK   via roach1  (  14.9ms)  -> connection pool exhaustion
[02:58:58] OK   via roach2  (  12.7ms)  -> connection pool exhaustion
[02:58:59] OK   via roach3  (   5.0ms)  -> connection pool exhaustion
[02:59:00] OK   via roach1  (   6.1ms)  -> connection pool exhaustion
                              # <- roach2 stopped here
[02:59:01] FAIL via roach2  -> connection to server at "localhost" ... server is not accepting clients, try another node
[02:59:02] OK   via roach3  (   8.7ms)  -> connection pool exhaustion
[02:59:03] OK   via roach1  (   5.5ms)  -> connection pool exhaustion
[02:59:08] FAIL via roach2  -> Connection refused ... Is the server running on that host?
[02:59:09] OK   via roach3  (   7.6ms)  -> connection pool exhaustion
[02:59:10] OK   via roach1  (  29.0ms)  -> connection pool exhaustion
                              # <- roach2 restarted here
[02:59:23] OK   via roach3  (  18.9ms)  -> connection pool exhaustion
[02:59:24] OK   via roach1  (  14.4ms)  -> connection pool exhaustion
[02:59:29] OK   via roach2  (3884.9ms)  -> connection pool exhaustion   # rejoining, slow first query
[02:59:30] OK   via roach3  (   6.9ms)  -> connection pool exhaustion
[02:59:31] OK   via roach1  (   8.4ms)  -> connection pool exhaustion
[02:59:32] OK   via roach2  (  16.5ms)  -> connection pool exhaustion  # fully recovered
```

## Alternative: GitHub Codespaces (no desktop install)

`.devcontainer/devcontainer.json` at the repo root is configured for this,
but in our own testing the Docker-in-Docker feature did not reliably
attach inside a Codespace even after a container rebuild — Docker
Desktop on your own machine is the path we actually verified working.
If you want to try Codespaces anyway: **Code → Create codespace on
master**, then the same commands above should work once `docker
--version` succeeds inside it.
