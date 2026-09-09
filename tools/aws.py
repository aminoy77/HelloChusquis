"""AWS integration with bounded CLI execution and private Lambda payloads."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace

import httpx


PLUGIN_NAME = "aws"
PLUGIN_DESCRIPTION = "Interact with AWS services - EC2, S3, Lambda, IAM"
AWSCLI_TIMEOUT_SECONDS = 60
AWSCLI_OUTPUT_MAX_CHARS = 4_096
LAMBDA_PAYLOAD_MAX_CHARS = 65_536

AWS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "aws",
        "description": "Perform AWS operations like listing EC2 instances, S3 buckets, invoking Lambda, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list_ec2", "list_s3", "list_lambda", "invoke_lambda", "list_iam", "describe_regions", "sts_caller"],
                    "description": "The AWS action to perform",
                },
                "resource": {"type": "string", "description": "Resource ID or name"},
                "region": {"type": "string", "description": "AWS region (default: us-east-1)"},
                "payload": {"type": "string", "description": "JSON payload for Lambda invocation"},
            },
            "required": ["action"],
        },
    },
}


def get_aws_credentials() -> dict[str, str | None]:
    """Get AWS credentials from environment."""
    return {
        "access_key": os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_ACCESS_KEY"),
        "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("AWS_SECRET_KEY"),
        "region": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    }


def aws_request(method: str, url: str, creds: dict[str, str | None], data: dict | None = None) -> str:
    """Make an AWS API request through a configured proxy."""
    proxy_url = os.getenv("AWS_API_PROXY") or os.getenv("AWS_PROXY_URL")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {creds['access_key']}:{creds['secret_key']}",
    }
    if not proxy_url:
        return "Error: Direct AWS API not supported. Configure AWS_API_PROXY or use boto3 locally."

    try:
        with httpx.Client(timeout=30, follow_redirects=False) as client:
            full_url = f"{proxy_url}{url}"
            response = client.get(full_url, headers=headers) if method == "GET" else client.post(full_url, headers=headers, json=data)
        if response.status_code in (200, 201):
            try:
                return _limit_output(json.dumps(response.json(), indent=2))
            except ValueError:
                return _limit_output(response.text)
        return f"Error: {response.status_code} - {_limit_output(response.text, 500)}"
    except httpx.HTTPError as exc:
        return f"Error: {exc}"


def _limit_output(value: str, maximum: int = AWSCLI_OUTPUT_MAX_CHARS) -> str:
    """Bound untrusted command or remote output retained by the agent."""
    return value[:maximum]


def _run_aws_cli(command: list[str]) -> SimpleNamespace:
    """Execute AWS CLI with bounded time and retained output."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=AWSCLI_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return SimpleNamespace(
            returncode=124,
            stdout="",
            stderr=f"AWS CLI timed out after {AWSCLI_TIMEOUT_SECONDS} seconds",
        )
    return SimpleNamespace(
        returncode=result.returncode,
        stdout=_limit_output(result.stdout),
        stderr=_limit_output(result.stderr),
    )


def _cli_error(result: SimpleNamespace) -> str:
    return f"Error: {result.stderr or 'AWS CLI command failed'}"


def _parse_json(stdout: str) -> dict:
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _invoke_lambda(resource: str, region: str, payload: str) -> str:
    if not resource:
        return "Error: resource (function name) required for invoke_lambda"
    if len(payload) > LAMBDA_PAYLOAD_MAX_CHARS:
        return f"Error: payload exceeds {LAMBDA_PAYLOAD_MAX_CHARS} characters"
    try:
        payload_value = json.loads(payload) if payload else {}
    except json.JSONDecodeError:
        return "Error: payload must be valid JSON"

    descriptor, temporary_path = tempfile.mkstemp(prefix="hellochusquis-aws-", suffix=".json")
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as payload_file:
            json.dump(payload_value, payload_file)
            payload_file.flush()
        result = _run_aws_cli([
            "aws", "lambda", "invoke",
            "--function-name", resource,
            "--payload", f"fileb://{temporary_path}",
            "--cli-binary-format", "raw-in-base64-out",
            "--region", region,
            "--log-type", "Tail",
            "--output", "json",
        ])
        if result.returncode == 0:
            return f"Lambda invoked!\n{_limit_output(result.stdout, 300)}"
        return _cli_error(result)
    finally:
        try:
            Path(temporary_path).unlink()
        except FileNotFoundError:
            pass


def run(action: str, resource: str = "", region: str = "us-east-1", payload: str = "") -> str:
    """Execute bounded AWS operations through the AWS CLI."""
    credentials = get_aws_credentials()
    if not credentials["access_key"]:
        return "Error: AWS credentials not found. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."

    try:
        if action == "list_ec2":
            result = _run_aws_cli(["aws", "ec2", "describe-instances", "--region", region, "--output", "json"])
            if result.returncode != 0:
                return _cli_error(result)
            instances = _parse_json(result.stdout).get("Reservations", [])
            labels = []
            for reservation in instances:
                for instance in reservation.get("Instances", []):
                    name = next((tag.get("Value", "N/A") for tag in instance.get("Tags", []) if tag.get("Key") == "Name"), instance.get("InstanceId"))
                    labels.append(f"• {name} [{instance.get('State', {}).get('Name', 'N/A')}] {instance.get('InstanceType', 'N/A')}")
            return _limit_output("\n".join(labels), 500) if labels else "No instances found."

        if action == "list_s3":
            result = _run_aws_cli(["aws", "s3", "ls", "--region", region])
            return _limit_output(result.stdout, 500) or "No buckets found." if result.returncode == 0 else _cli_error(result)

        if action == "list_lambda":
            result = _run_aws_cli(["aws", "lambda", "list-functions", "--region", region, "--output", "json"])
            if result.returncode != 0:
                return _cli_error(result)
            functions = _parse_json(result.stdout).get("Functions", [])
            labels = [f"• {function.get('FunctionName')} ({function.get('Runtime', 'N/A')})" for function in functions[:10]]
            return "\n".join(labels) if labels else "No functions found."

        if action == "invoke_lambda":
            return _invoke_lambda(resource, region, payload)

        if action == "list_iam":
            result = _run_aws_cli(["aws", "iam", "list-users", "--max-items", "10", "--output", "json"])
            if result.returncode != 0:
                return _cli_error(result)
            users = _parse_json(result.stdout).get("Users", [])
            labels = [f"• {user.get('UserName')} (created: {user.get('CreateDate', 'N/A')})" for user in users]
            return "\n".join(labels) if labels else "No users found."

        if action == "describe_regions":
            result = _run_aws_cli(["aws", "ec2", "describe-regions", "--output", "json"])
            if result.returncode != 0:
                return _cli_error(result)
            regions = _parse_json(result.stdout).get("Regions", [])
            return "\n".join(f"• {item.get('RegionName')} ({item.get('Endpoint', 'N/A')})" for item in regions[:10])

        if action == "sts_caller":
            result = _run_aws_cli(["aws", "sts", "get-caller-identity", "--output", "json"])
            if result.returncode != 0:
                return _cli_error(result)
            identity = _parse_json(result.stdout)
            return f"Account: {identity.get('Account')}\nUser: {identity.get('UserId')}\nARN: {identity.get('Arn')}"

        return f"Error: Unknown action '{action}'. Available: list_ec2, list_s3, list_lambda, invoke_lambda, list_iam, describe_regions, sts_caller"
    except FileNotFoundError:
        return "Error: AWS CLI not installed. Install: brew install awscli"
    except OSError as exc:
        return f"Error: AWS CLI execution failed: {exc}"


if __name__ == "__main__":
    print("AWS plugin loaded. Use 'aws' tool in HelloChusquis.")
