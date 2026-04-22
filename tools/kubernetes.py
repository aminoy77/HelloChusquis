from tools.base import BaseTool, ToolResult
import httpx
import os
import json


PLUGIN_NAME = "kubernetes"
PLUGIN_DESCRIPTION = "Manage Kubernetes clusters"

KUBERNETES_SCHEMA = {
    "type": "function",
    "function": {
        "name": "kubernetes",
        "description": "K8s operations - pods, deployments, services",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["pods", "deployments", "services", "apply", "delete", "logs", "exec", "scale"]},
                "namespace": {"type": "string", "description": "Namespace"},
                "resource": {"type": "string", "description": "Resource name"},
                "yaml": {"type": "string", "description": "YAML manifest"},
                "replicas": {"type": "number", "description": "Number of replicas"},
            },
            "required": ["action"]
        }
    }
}


def run(action: str, namespace: str = "default", resource: str = "", yaml: str = "", replicas: int = 0) -> str:
    """Kubernetes operations via kubectl."""
    kubeconfig = os.getenv("KUBECONFIG")
    
    cmd = ["kubectl"]
    if kubeconfig:
        cmd.extend(["--kubeconfig", kubeconfig])
    
    if namespace and namespace != "default":
        cmd.extend(["-n", namespace])
    
    if action == "pods":
        cmd.extend(["get", "pods"])
    elif action == "deployments":
        cmd.extend(["get", "deployments"])
    elif action == "services":
        cmd.extend(["get", "services"])
    elif action == "apply":
        if yaml:
            # Write YAML to tmp and apply
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(yaml)
                f.flush()
                cmd.extend(["apply", "-f", f.name])
                import subprocess
                result = subprocess.run(cmd, capture_output=True, text=True)
                return result.stdout + result.stderr
        return "Error: yaml required"
    elif action == "delete":
        cmd.extend(["delete", resource, "--ignore-not-found"])
    elif action == "logs":
        cmd.extend(["logs", resource, "--tail=50"])
    elif action == "scale":
        cmd.extend(["scale", f"deployment/{resource}", f"--replicas={replicas}"])
    else:
        return f"Unknown action: {action}"
    
    import subprocess
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout or result.stderr


if __name__ == "__main__":
    print("Kubernetes plugin loaded.")