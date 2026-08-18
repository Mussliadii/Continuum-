import os

import certifi
import psycopg2

# Loading .env is a local-dev concern only (Lambda gets real env vars from its
# configuration) — the load_dotenv() call lives in each local entry point
# (scripts/*.py, local_server.py), not here, so this module stays
# import-clean for the Lambda deployment package.


def get_connection():
    url = os.environ["COCKROACHDB_URL"]
    return psycopg2.connect(url, sslrootcert=certifi.where(), connect_timeout=10)
