"""Apply backend/db/schema.sql to the CockroachDB cluster configured in .env."""

import pathlib
import sys

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "backend" / "src"))

from db import get_connection  # noqa: E402

SCHEMA_PATH = pathlib.Path(__file__).resolve().parent.parent / "backend" / "db" / "schema.sql"


def main():
    sql = SCHEMA_PATH.read_text()
    conn = get_connection()
    conn.autocommit = True
    cur = conn.cursor()
    for statement in filter(None, (s.strip() for s in sql.split(";"))):
        # Chunks may carry a leading `--` comment line from the .sql file;
        # the DB parser ignores it, so just check there's real SQL after it.
        code_only = "\n".join(
            line for line in statement.splitlines() if not line.strip().startswith("--")
        ).strip()
        if not code_only:
            continue
        cur.execute(statement)
        print(f"OK: {code_only[:70]}")
    cur.close()
    conn.close()
    print("Schema applied successfully.")


if __name__ == "__main__":
    main()
