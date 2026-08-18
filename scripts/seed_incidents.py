"""Seed the `incidents` knowledge base with realistic past incidents.

Each incident's title + description + tags are embedded (as a
RETRIEVAL_DOCUMENT) and stored alongside the root cause and resolution, so
that a live incident description can later be matched against this history
via cosine similarity search.

Usage:
    python scripts/seed_incidents.py
"""

import pathlib
import sys

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "backend" / "src"))

from db import get_connection  # noqa: E402
from embeddings import embed_document, to_pgvector_literal  # noqa: E402

INCIDENTS = [
    {
        "title": "Connection pool exhaustion under traffic spike",
        "description": "API p99 latency jumped from 80ms to 4s during a marketing campaign spike. Requests queued waiting for a free database connection.",
        "root_cause": "Connection pool max size (20) was sized for baseline traffic, not campaign-level bursts.",
        "resolution": "Raised pool max_conns to 200 and added a queue-depth alert to catch this earlier next time.",
        "severity": "critical",
        "tags": ["database", "latency", "connection-pool"],
    },
    {
        "title": "Disk full on log volume",
        "description": "Write requests started failing with I/O errors. Node health check flagged the data disk at 100% capacity.",
        "root_cause": "Log rotation cron job silently stopped running after a package upgrade changed the binary path.",
        "resolution": "Fixed the logrotate cron path and added a disk-usage alert at 80% threshold.",
        "severity": "critical",
        "tags": ["disk", "ops", "logging"],
    },
    {
        "title": "Gradual memory leak causing OOM kills",
        "description": "Service pods were being OOM-killed roughly every 6 hours, each time after a slow climb in RSS memory usage.",
        "root_cause": "A metrics client library was leaking connection objects on every request due to a missing close() call.",
        "resolution": "Upgraded the metrics client to a patched version and added a memory-growth-rate alert.",
        "severity": "warning",
        "tags": ["memory", "leak", "kubernetes"],
    },
    {
        "title": "TLS certificate expired on public API gateway",
        "description": "All external API calls started failing with SSL handshake errors at midnight UTC.",
        "root_cause": "Certificate auto-renewal job had insufficient IAM permissions after a policy change and failed silently for weeks.",
        "resolution": "Rotated the certificate manually and fixed the renewal job's IAM role; added a cert-expiry-in-14-days alert.",
        "severity": "critical",
        "tags": ["tls", "certificates", "networking"],
    },
    {
        "title": "Bad deploy caused 500s on checkout flow",
        "description": "Error rate on the checkout endpoint jumped to 40% within two minutes of a routine deploy.",
        "root_cause": "A null-pointer bug in a new feature flag branch that was accidentally enabled for 100% of traffic.",
        "resolution": "Rolled back the deploy and fixed the feature-flag default to off before re-releasing.",
        "severity": "critical",
        "tags": ["deployment", "regression", "checkout"],
    },
    {
        "title": "Cache stampede after cache cluster restart",
        "description": "Database CPU spiked to 100% for several minutes right after a scheduled cache cluster maintenance restart.",
        "root_cause": "All cache keys expired simultaneously on restart, so every request fell through to the database at once.",
        "resolution": "Added jittered TTLs and a request-coalescing lock so only one request repopulates a given key.",
        "severity": "warning",
        "tags": ["cache", "database", "thundering-herd"],
    },
    {
        "title": "Slow query from missing index after schema migration",
        "description": "A specific report page timed out for all users starting right after a migration ran.",
        "root_cause": "The migration dropped an index that a hot query path depended on; the query planner fell back to a full table scan.",
        "resolution": "Re-created the index and added a migration checklist step to diff query plans before/after.",
        "severity": "warning",
        "tags": ["database", "migration", "query-performance"],
    },
    {
        "title": "Regional network partition isolated one availability zone",
        "description": "Nodes in one AZ stopped receiving traffic; cross-AZ replication lag alerts fired simultaneously.",
        "root_cause": "A misconfigured route table change isolated the AZ's subnet from the rest of the VPC.",
        "resolution": "Reverted the route table change and added a canary health check per AZ before route changes roll out.",
        "severity": "critical",
        "tags": ["networking", "availability-zone", "infrastructure"],
    },
    {
        "title": "Rate limiter misconfiguration blocked legitimate traffic",
        "description": "A subset of enterprise customers reported 429 errors on every request starting after a config deploy.",
        "root_cause": "A new per-IP rate limit rule didn't account for customers behind a shared NAT gateway.",
        "resolution": "Switched enterprise-tier rate limiting to an API-key basis instead of source IP.",
        "severity": "warning",
        "tags": ["rate-limiting", "networking", "customer-impact"],
    },
    {
        "title": "Third-party payment provider outage",
        "description": "Checkout success rate dropped to near zero; error logs showed timeouts calling the payment provider's API.",
        "root_cause": "Upstream payment provider had a regional outage; our circuit breaker was not tripping fast enough.",
        "resolution": "Tuned the circuit breaker thresholds and added a secondary payment provider as fallback.",
        "severity": "critical",
        "tags": ["third-party", "payments", "circuit-breaker"],
    },
    {
        "title": "Load balancer health check flapping",
        "description": "Instances were repeatedly marked unhealthy and removed from rotation for a few seconds at a time, causing intermittent 502s.",
        "root_cause": "Health check timeout (1s) was too aggressive for a GC pause pattern in the JVM-based service.",
        "resolution": "Increased health check timeout to 5s and tuned JVM GC settings to reduce pause duration.",
        "severity": "warning",
        "tags": ["load-balancer", "jvm", "health-check"],
    },
    {
        "title": "Message queue backlog growing unbounded",
        "description": "Consumer lag on the order-processing queue grew steadily over two hours, delaying order confirmations.",
        "root_cause": "A downstream consumer was deployed with a bug that caused it to silently drop its connection every few minutes.",
        "resolution": "Fixed the consumer's reconnect logic and added a consumer-lag alert with a runbook link.",
        "severity": "warning",
        "tags": ["message-queue", "consumer-lag", "orders"],
    },
    {
        "title": "Expired secret broke service-to-service auth",
        "description": "Internal service calls between the billing and notifications services started failing with 401s.",
        "root_cause": "A shared secret used for internal JWT signing expired and the rotation automation only updated one of the two services.",
        "resolution": "Rotated the secret on both services and moved to a secret-manager-based rotation that updates all consumers atomically.",
        "severity": "critical",
        "tags": ["auth", "secrets", "service-to-service"],
    },
    {
        "title": "Autoscaler thrashing during traffic ramp-up",
        "description": "Pods were rapidly scaled up and down every 30 seconds during a gradual traffic increase, causing request errors during each transition.",
        "root_cause": "The autoscaler's target CPU threshold and cooldown period were too tight for the workload's burstiness.",
        "resolution": "Widened the cooldown window and switched to a request-rate-based scaling metric instead of CPU.",
        "severity": "warning",
        "tags": ["autoscaling", "kubernetes", "capacity"],
    },
    {
        "title": "Noisy neighbor caused CPU steal on shared host",
        "description": "One service's latency degraded intermittently with no corresponding change in its own request volume or code.",
        "root_cause": "A co-located batch job on the same host was consuming most of the CPU, causing CPU steal time for other tenants.",
        "resolution": "Moved the batch job to a dedicated node pool with resource limits enforced.",
        "severity": "warning",
        "tags": ["infrastructure", "noisy-neighbor", "cpu"],
    },
    {
        "title": "Clock skew broke distributed lock expiry",
        "description": "Two workers both believed they held the same distributed lock at the same time, causing a duplicate job run.",
        "root_cause": "NTP sync had drifted on one host by several seconds, breaking the lock's time-based expiry assumption.",
        "resolution": "Fixed the NTP configuration on the affected host and added a clock-skew alert across the fleet.",
        "severity": "warning",
        "tags": ["distributed-systems", "clock-skew", "locking"],
    },
    {
        "title": "Deadlock between two services under high concurrency",
        "description": "Both services stopped processing requests entirely; thread dumps showed each waiting on a lock held by the other.",
        "root_cause": "A newly added synchronous callback introduced a circular wait between two previously independent lock paths.",
        "resolution": "Removed the circular dependency by making the callback asynchronous, and added a deadlock-detection timeout as a safety net.",
        "severity": "critical",
        "tags": ["concurrency", "deadlock", "architecture"],
    },
    {
        "title": "Failed region failover left traffic split during maintenance",
        "description": "During a planned regional maintenance window, a portion of traffic kept routing to the region being drained.",
        "root_cause": "DNS TTL for the regional endpoint was set too high, so some resolvers kept serving the old region long after the failover.",
        "resolution": "Lowered the DNS TTL ahead of planned maintenance windows and added a traffic-drain verification step to the runbook.",
        "severity": "warning",
        "tags": ["dns", "failover", "maintenance"],
    },
]


def main():
    conn = get_connection()
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("SELECT count(*) FROM incidents")
    existing = cur.fetchone()[0]
    if existing > 0:
        print(f"incidents table already has {existing} rows. Skipping seed to avoid duplicates.")
        print("Run `DELETE FROM incidents;` first if you want to reseed from scratch.")
        cur.close()
        conn.close()
        return

    for incident in INCIDENTS:
        embedding_text = f"{incident['title']}. {incident['description']} Tags: {', '.join(incident['tags'])}"
        vector = embed_document(embedding_text)
        cur.execute(
            """
            INSERT INTO incidents (title, description, root_cause, resolution, severity, tags, embedding, resolved_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, now())
            """,
            (
                incident["title"],
                incident["description"],
                incident["root_cause"],
                incident["resolution"],
                incident["severity"],
                incident["tags"],
                to_pgvector_literal(vector),
            ),
        )
        print(f"Seeded: {incident['title']}")

    cur.close()
    conn.close()
    print(f"Done. Seeded {len(INCIDENTS)} incidents.")


if __name__ == "__main__":
    main()
