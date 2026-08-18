"""Build the Lambda deployment package (dist/lambda.zip).

Developing on Windows but deploying to Lambda (Amazon Linux, x86_64) means
we can't just `pip install` locally — psycopg2-binary and other deps have
native extensions that would be built for the wrong platform. Instead we
ask pip for manylinux wheels explicitly; no Docker or AWS CLI required.

Usage:
    python scripts/build_lambda_package.py
"""

import pathlib
import shutil
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
BACKEND_SRC = ROOT / "backend" / "src"
REQUIREMENTS = ROOT / "backend" / "requirements.txt"
BUILD_DIR = ROOT / "build" / "lambda_package"
DIST_ZIP = ROOT / "dist" / "lambda.zip"

# Must match the Lambda function's configured runtime (see deploy_lambda.py).
PYTHON_VERSION = "3.12"
ABI = "cp312"
PLATFORM = "manylinux2014_x86_64"


def main():
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)
    DIST_ZIP.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading Linux ({PLATFORM}, Python {PYTHON_VERSION}) wheels for Lambda...")
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install",
            "-r", str(REQUIREMENTS),
            "--target", str(BUILD_DIR),
            "--platform", PLATFORM,
            "--python-version", PYTHON_VERSION,
            "--implementation", "cp",
            "--abi", ABI,
            "--only-binary=:all:",
            "--no-compile",
        ],
        check=True,
    )

    print("Copying application source...")
    local_dev_only = {"local_server.py"}
    for py_file in BACKEND_SRC.glob("*.py"):
        if py_file.name not in local_dev_only:
            shutil.copy(py_file, BUILD_DIR / py_file.name)

    print(f"Zipping to {DIST_ZIP}...")
    if DIST_ZIP.exists():
        DIST_ZIP.unlink()
    with zipfile.ZipFile(DIST_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in BUILD_DIR.rglob("*"):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(BUILD_DIR))

    size_mb = DIST_ZIP.stat().st_size / (1024 * 1024)
    print(f"Done. {DIST_ZIP} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
