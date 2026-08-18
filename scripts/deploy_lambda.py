"""Deploy the Lambda function and its API Gateway HTTP API front door.

No AWS CLI or Docker required — this uses boto3 directly against
credentials already configured in the environment (env vars, `~/.aws/credentials`,
or an assumed role). Region defaults to ap-southeast-3 to match the
CockroachDB cluster's region for low latency.

Run scripts/build_lambda_package.py first to produce dist/lambda.zip.

Usage:
    python scripts/deploy_lambda.py
"""

import json
import os
import pathlib
import time

import boto3
from dotenv import load_dotenv

load_dotenv()

REGION = os.environ.get("AWS_REGION", "ap-southeast-3")
FUNCTION_NAME = "continuum-agent"
ROLE_NAME = "continuum-lambda-role"
API_NAME = "continuum-api"
ZIP_PATH = pathlib.Path(__file__).resolve().parent.parent / "dist" / "lambda.zip"

TRUST_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}
    ],
}

ENV_VAR_NAMES = [
    "COCKROACHDB_URL",
    "COCKROACHDB_MCP_ENDPOINT",
    "COCKROACHDB_MCP_SERVICE_ACCOUNT_KEY",
    "GROQ_API_KEY",
    "GEMINI_API_KEY",
]


def ensure_role(iam) -> str:
    try:
        role = iam.get_role(RoleName=ROLE_NAME)
        return role["Role"]["Arn"]
    except iam.exceptions.NoSuchEntityException:
        pass

    role = iam.create_role(RoleName=ROLE_NAME, AssumeRolePolicyDocument=json.dumps(TRUST_POLICY))
    iam.attach_role_policy(
        RoleName=ROLE_NAME,
        PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    )
    print(f"Created IAM role {ROLE_NAME}, waiting for IAM propagation...")
    time.sleep(10)
    return role["Role"]["Arn"]


def ensure_function(lambda_client, role_arn: str, env_vars: dict) -> str:
    zip_bytes = ZIP_PATH.read_bytes()

    try:
        lambda_client.get_function(FunctionName=FUNCTION_NAME)
        exists = True
    except lambda_client.exceptions.ResourceNotFoundException:
        exists = False

    if exists:
        print(f"Updating existing function {FUNCTION_NAME}...")
        lambda_client.update_function_code(FunctionName=FUNCTION_NAME, ZipFile=zip_bytes)
        lambda_client.get_waiter("function_updated").wait(FunctionName=FUNCTION_NAME)
        lambda_client.update_function_configuration(
            FunctionName=FUNCTION_NAME,
            Environment={"Variables": env_vars},
            Timeout=60,
            MemorySize=512,
        )
    else:
        print(f"Creating function {FUNCTION_NAME}...")
        lambda_client.create_function(
            FunctionName=FUNCTION_NAME,
            Runtime="python3.12",
            Role=role_arn,
            Handler="handler.lambda_handler",
            Code={"ZipFile": zip_bytes},
            Timeout=60,
            MemorySize=512,
            Environment={"Variables": env_vars},
        )

    lambda_client.get_waiter("function_active").wait(FunctionName=FUNCTION_NAME)
    return lambda_client.get_function(FunctionName=FUNCTION_NAME)["Configuration"]["FunctionArn"]


def ensure_http_api(apigw, lambda_client, function_arn: str) -> str:
    """Quick-create an HTTP API with a $default catch-all route to the Lambda.

    handler.py does its own routing from `rawPath`, so a single proxy
    route is enough — no per-path API Gateway resources to configure.
    """
    existing = next((a for a in apigw.get_apis()["Items"] if a["Name"] == API_NAME), None)

    if existing is None:
        print(f"Creating HTTP API {API_NAME}...")
        api = apigw.create_api(Name=API_NAME, ProtocolType="HTTP", Target=function_arn)
        api_id = api["ApiId"]
    else:
        print(f"HTTP API {API_NAME} already exists.")
        api_id = existing["ApiId"]

    account_id = boto3.client("sts", region_name=REGION).get_caller_identity()["Account"]
    source_arn = f"arn:aws:execute-api:{REGION}:{account_id}:{api_id}/*/*"
    try:
        lambda_client.add_permission(
            FunctionName=FUNCTION_NAME,
            StatementId="apigateway-invoke",
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=source_arn,
        )
    except lambda_client.exceptions.ResourceConflictException:
        pass  # permission already granted from a prior deploy

    return f"https://{api_id}.execute-api.{REGION}.amazonaws.com"


def main():
    missing = [name for name in ENV_VAR_NAMES if not os.environ.get(name)]
    if missing:
        raise SystemExit(f"Missing required environment variables: {missing}")
    if not ZIP_PATH.exists():
        raise SystemExit(f"{ZIP_PATH} not found — run scripts/build_lambda_package.py first.")

    session = boto3.Session(region_name=REGION)
    iam = session.client("iam")
    lambda_client = session.client("lambda")
    apigw = session.client("apigatewayv2")

    role_arn = ensure_role(iam)
    env_vars = {name: os.environ[name] for name in ENV_VAR_NAMES}
    function_arn = ensure_function(lambda_client, role_arn, env_vars)
    invoke_url = ensure_http_api(apigw, lambda_client, function_arn)

    print()
    print(f"Deployed. API base URL: {invoke_url}")
    print(f"Try: curl -X POST {invoke_url}/chat -H 'Content-Type: application/json' -d '{{\"message\": \"test\"}}'")


if __name__ == "__main__":
    main()
