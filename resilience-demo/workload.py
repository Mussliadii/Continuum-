"""Continuous query workload against the local 3-node cluster.

Run this in its own terminal while you kill/restart a node in another one.
It prints one line per second: a timestamp, whether the query succeeded,
and which node answered — the visual proof that the cluster keeps serving
reads/writes through a node failure.

Usage:
    python3 workload.py
"""

import sys
import time

import psycopg2

# Round-robins across all three published SQL ports so a killed node's
# port failing doesn't take the whole demo down — mirrors how a real
# client with multiple connection endpoints would behave.
CONNECTIONS = [
    ("roach1", "postgresql://root@localhost:26257/defaultdb?sslmode=disable"),
    ("roach2", "postgresql://root@localhost:26258/defaultdb?sslmode=disable"),
    ("roach3", "postgresql://root@localhost:26259/defaultdb?sslmode=disable"),
]


def setup():
    conn = psycopg2.connect(CONNECTIONS[0][1])
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS demo_incidents (id INT PRIMARY KEY, title STRING)")
    cur.execute(
        "UPSERT INTO demo_incidents (id, title) VALUES (1, 'connection pool exhaustion')"
    )
    cur.close()
    conn.close()


def main():
    setup()
    print("Workload running. Ctrl+C to stop.\n")
    i = 0
    while True:
        i += 1
        node_name, dsn = CONNECTIONS[i % len(CONNECTIONS)]
        start = time.time()
        try:
            conn = psycopg2.connect(dsn, connect_timeout=3)
            cur = conn.cursor()
            cur.execute("SELECT title FROM demo_incidents WHERE id = 1")
            row = cur.fetchone()
            cur.close()
            conn.close()
            elapsed_ms = (time.time() - start) * 1000
            print(f"[{time.strftime('%H:%M:%S')}] OK   via {node_name:<7} ({elapsed_ms:6.1f}ms)  -> {row[0]}", flush=True)
        except Exception as exc:  # noqa: BLE001 — expected while a node is down; the point of the demo
            print(f"[{time.strftime('%H:%M:%S')}] FAIL via {node_name:<7} -> {exc}", flush=True)
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
