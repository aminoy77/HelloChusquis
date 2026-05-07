from tools.base import BaseTool, ToolResult
import httpx
import os
import json
import base64


PLUGIN_NAME = "aws"
PLUGIN_DESCRIPTION = "Interact with AWS services - EC2, S3, Lambda, IAM"

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
                    "description": "The AWS action to perform"
                },
                "resource": {"type": "string", "description": "Resource ID or name"},
                "region": {"type": "string", "description": "AWS region (default: us-east-1)"},
                "payload": {"type": "string", "description": "JSON payload for Lambda invocation"},
            },
            "required": ["action"]
        }
    }
}


def get_aws_credentials() -> dict:
    """Get AWS credentials from environment."""
    return {
        "access_key": os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_ACCESS_KEY"),
        "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("AWS_SECRET_KEY"),
        "region": os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    }


def aws_request(method: str, url: str, creds: dict, data: dict = None) -> str:
    """Make AWS API request using IAM auth (or proxy)."""
    # This is a simplified version - in production you'd use boto3
    # Check for proxy endpoint
    proxy_url = os.getenv("AWS_API_PROXY") or os.getenv("AWS_PROXY_URL")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {creds['access_key']}:{creds['secret_key']}"
    }
    
    try:
        client = httpx.Client(timeout=30)
        
        if proxy_url:
            # Use proxy (e.g., localstack, AWS API Gateway)
            full_url = f"{proxy_url}{url}"
            if method == "GET":
                resp = client.get(full_url, headers=headers)
            else:
                resp = client.post(full_url, headers=headers, json=data)
        else:
            # Direct AWS API (needs proper signing - simplified here)
            # Use AWS CLI if available
            return "Error: Direct AWS API not supported. Configure AWS_API_PROXY or use boto3 locally."
        
        if resp.status_code in [200, 201]:
            try:
                return json.dumps(resp.json(), indent=2)[:1000]
            except Exception:
                return resp.text[:500]
        return f"Error: {resp.status_code} - {resp.text[:200]}"
    
    except Exception as e:
        return f"Error: {str(e)}"


def run(action: str, resource: str = "", region: str = "us-east-1", payload: str = "") -> str:
    """Execute AWS operations."""
    creds = get_aws_credentials()
    if not creds["access_key"]:
        return "Error: AWS credentials not found. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."
    
    # Build URL based on action
    base_url = f"https://{region}.amazonaws.com"
    
    try:
        client = httpx.Client(timeout=30)
        
        if action == "list_ec2":
            # Try AWS CLI first (most reliable)
            import subprocess
            result = subprocess.run(
                ["aws", "ec2", "describe-instances", "--region", region, "--output", "json"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                instances = data.get("Reservations", [])
                result_text = []
                for r in instances:
                    for i in r.get("Instances", []):
                        name = next((t.get("Value", "N/A") for t in i.get("Tags", []) if t.get("Key") == "Name"), i.get("InstanceId"))
                        result_text.append(f"• {name} [{i.get('State', {}).get('Name', 'N/A')}] {i.get('InstanceType', 'N/A')}")
                return "\n".join(result_text)[:500] if result_text else "No instances found."
            return f"Error: {result.stderr}"
        
        elif action == "list_s3":
            import subprocess
            result = subprocess.run(
                ["aws", "s3", "ls", "--region", region],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                return result.stdout[:500] or "No buckets found."
            return f"Error: {result.stderr}"
        
        elif action == "list_lambda":
            import subprocess
            result = subprocess.run(
                ["aws", "lambda", "list-functions", "--region", region, "--output", "json"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                funcs = data.get("Functions", [])
                result_text = []
                for f in funcs[:10]:
                    result_text.append(f"• {f.get('FunctionName')} ({f.get('Runtime', 'N/A')})")
                return "\n".join(result_text) if result_text else "No functions found."
            return f"Error: {result.stderr}"
        
        elif action == "invoke_lambda":
            if not resource:
                return "Error: resource (function name) required for invoke_lambda"
            
            import subprocess
            
            invoke_data = {}
            if payload:
                try:
                    invoke_data = json.loads(payload)
                except Exception:
                    pass
            
            # Convert to JSON string for CLI
            payload_arg = json.dumps(invoke_data) if invoke_data else '{}'
            
            result = subprocess.run(
                ["aws", "lambda", "invoke", 
                 "--function-name", resource,
                 "--payload", payload_arg,
                 "--region", region,
                 "--log-type", "Tail",
                 "--output", "json"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                # Parse response
                return f"Lambda invoked! :white_check_mark:\n{result.stdout[:300]}"
            return f"Error: {result.stderr}"
        
        elif action == "list_iam":
            import subprocess
            result = subprocess.run(
                ["aws", "iam", "list-users", "--max-items", "10", "--output", "json"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                users = data.get("Users", [])
                result_text = []
                for u in users:
                    result_text.append(f"• {u.get('UserName')} (created: {u.get('CreateDate', 'N/A')})")
                return "\n".join(result_text) if result_text else "No users found."
            return f"Error: {result.stderr}"
        
        elif action == "describe_regions":
            import subprocess
            result = subprocess.run(
                ["aws", "ec2", "describe-regions", "--output", "json"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                regions = data.get("Regions", [])
                result_text = [f"• {r.get('RegionName')} ({r.get('Endpoint', 'N/A')})" for r in regions[:10]]
                return "\n".join(result_text)
            return f"Error: {result.stderr}"
        
        elif action == "sts_caller":
            import subprocess
            result = subprocess.run(
                ["aws", "sts", "get-caller-identity", "--output", "json"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return f"Account: {data.get('Account')}\nUser: {data.get('UserId')}\nARN: {data.get('Arn')}"
            return f"Error: {result.stderr}"
        
        else:
            return f"Error: Unknown action '{action}'. Available: list_ec2, list_s3, list_lambda, invoke_lambda, list_iam, describe_regions, sts_caller"
    
    except FileNotFoundError:
        return "Error: AWS CLI not installed. Install: brew install awscli"
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print("AWS plugin loaded. Use 'aws' tool in HelloChusquis.")