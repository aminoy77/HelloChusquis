"""Kubernetes integration with bounded kubectl execution."""

import os
from pathlib import Path
import subprocess
import tempfile


KUBERNETES_TIMEOUT_SECONDS = 120

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
            "required": ["action"],
        },
    },
}


def _run_kubectl(command: list[str]) -> str:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=KUBERNETES_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return f"kubectl timed out after {KUBERNETES_TIMEOUT_SECONDS} seconds"
    return result.stdout or result.stderr


def run(action: str, namespace: str = "default", resource: str = "", yaml: str = "", replicas: int = 0) -> str:
    """Run a bounded kubectl operation."""
    kubeconfig = os.getenv("KUBECONFIG")
    command = ["kubectl"]
    if kubeconfig:
        command.extend(["--kubeconfig", kubeconfig])
    if namespace and namespace != "default":
        command.extend(["-n", namespace])

    if action == "pods":
        command.extend(["get", "pods"])
    elif action == "deployments":
        command.extend(["get", "deployments"])
    elif action == "services":
        command.extend(["get", "services"])
    elif action == "apply":
        if not yaml:
            return "Error: yaml required"
        descriptor, temporary_path = tempfile.mkstemp(suffix=".yaml")
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(yaml)
                handle.flush()
            command.extend(["apply", "-f", temporary_path])
            return _run_kubectl(command)
        finally:
            try:
                Path(temporary_path).unlink()
            except FileNotFoundError:
                pass
    elif action == "delete":
        command.extend(["delete", resource, "--ignore-not-found"])
    elif action == "logs":
        command.extend(["logs", resource, "--tail=50"])
    elif action == "scale":
        command.extend(["scale", f"deployment/{resource}", f"--replicas={replicas}"])
    else:
        return f"Unknown action: {action}"
    return _run_kubectl(command)
