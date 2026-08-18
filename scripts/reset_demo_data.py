"""Reset transactional/demo state before recording the submission video.

Clears all active incidents and their event timelines, and trims the
`incidents` knowledge base back down to the original seed set (in case
testing added extra resolved incidents via the self-improving-memory loop).

Usage:
    python scripts/reset_demo_data.py
"""

import pathlib
import sys

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "backend" / "src"))

from db import get_connection  # noqa: E402
from seed_incidents import INCIDENTS  # noqa: E402


def main():
    conn = get_connection()
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("DELETE FROM incident_events")
    cur.execute("DELETE FROM active_incidents")
    print("Cleared active_incidents and incident_events.")

    seed_titles = tuple(i["title"] for i in INCIDENTS)
    cur.execute("DELETE FROM incidents WHERE title NOT IN %s", (seed_titles,))
    print(f"Trimmed incidents table back to the {len(seed_titles)} seeded rows.")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
