from tools.base import BaseTool, ToolResult
import httpx
import os


PLUGIN_NAME = "docker"
PLUGIN_DESCRIPTION = "Manage Docker containers, images, and volumes"

DOCKER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "docker",
        "description": "Perform Docker operations like listing containers, images, starting/stopping containers, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list_containers", "list_images", "list_volumes", "start_container", "stop_container", "remove_container", "container_logs", "docker_info", "prune_containers", "prune_images"],
                    "description": "The Docker action to perform"
                },
                "container": {"type": "string", "description": "Container name or ID"},
                "image": {"type": "string", "description": "Image name or ID"},
                "volume": {"type": "string", "description": "Volume name"},
                "all": {"type": "boolean", "description": "Show all (including stopped)"},
                "tail": {"type": "number", "description": "Number of log lines to show (default 50)"},
            },
            "required": ["action"]
        }
    }
}


def get_docker_host() -> str:
    """Get Docker host from environment."""
    return os.getenv("DOCKER_HOST") or os.getenv("DOCKER_API_URL")


def run(action: str, container: str = "", image: str = "", volume: str = "",
       all: bool = False, tail: int = 50) -> str:
    """Execute Docker API actions via Unix socket or TCP."""
    import socket
    
    try:
        # Try to use Docker socket
        socket_path = os.getenv("DOCKER_SOCKET_PATH", "/var/run/docker.sock")
        
        if not os.path.exists(socket_path):
            # Fallback: use TCP connection if available
            host = get_docker_host()
            if host:
                return f"TODO: TCP Docker connection to {host} not implemented yet"
            return "Error: Docker socket not found. Set DOCKER_SOCKET_PATH or DOCKER_HOST."
        
        # Use Unix socket for Docker API
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(socket_path)
        
        # Build Docker API request
        if action == "list_containers":
            path = f"/containers/json?all={all}"
        elif action == "list_images":
            path = "/images/json"
        elif action == "list_volumes":
            path = "/volumes"
        elif action == "docker_info":
            path = "/info"
        elif action == "start_container":
            if not container:
                return "Error: container name or ID required for start_container"
            path = f"/containers/{container}/start"
        elif action == "stop_container":
            if not container:
                return "Error: container name or ID required for stop_container"
            path = f"/containers/{container}/stop"
        elif action == "remove_container":
            if not container:
                return "Error: container name or ID required for remove_container"
            path = f"/containers/{container}?force=true"
        elif action == "container_logs":
            if not container:
                return "Error: container name or ID required for container_logs"
            path = f"/containers/{container}/logs?stdout=true&stderr=true&tail={tail}"
        elif action == "prune_containers":
            path = "/containers/prune"
        elif action == "prune_images":
            path = "/images/prune"
        else:
            return f"Error: Unknown action '{action}'"
        
        # Send HTTP request via Unix socket
        request = f"GET {path} HTTP/1.1\r\nHost: localhost\r\n\r\n"
        sock.sendall(request.encode())
        
        # Receive response
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
        
        sock.close()
        
        # Parse response
        if response:
            # Find body start (after headers)
            body_start = response.find(b"\r\n\r\n") + 4
            body = response[body_start:]
            
            import json
            try:
                data = json.loads(body)
                
                if action == "list_containers":
                    result = []
                    for c in data[:10]:
                        status = c.get("State", "")
                        names = c.get("Names", ["N/A"])
                        result.append(f"• {names[0].lstrip('/')} [{status}] {c.get('Image', 'N/A')}")
                    return "\n".join(result) if result else "No containers found."
                
                elif action == "list_images":
                    result = []
                    for i in data[:10]:
                        tags = i.get("RepoTags", ["<none>"])
                        result.append(f"• {tags[0]} ({i.get('Size', 'N/A')})")
                    return "\n".join(result) if result else "No images found."
                
                elif action == "list_volumes":
                    result = []
                    for v in data.get("Volumes", [])[:10]:
                        result.append(f"• {v.get('Name', 'N/A')}")
                    return "\n".join(result) if result else "No volumes found."
                
                elif action == "docker_info":
                    return f"Docker {data.get('ServerVersion')}\nContainers: {data.get('Containers')}\nImages: {data.get('Images')}"
                
                elif action in ["start_container", "stop_container", "remove_container"]:
                    if response.startswith(b"HTTP/1.1 204") or response.startswith(b"HTTP/1.1 200"):
                        return f"Action '{action}' completed! :white_check_mark:"
                    return f"Error: {response.decode()[:200]}"
                
                elif action == "container_logs":
                    return body.decode("utf-8", errors="ignore")[:1000]
                
                elif action in ["prune_containers", "prune_images"]:
                    freed = data.get("SpaceReclaimed", 0) if isinstance(data, dict) else 0
                    return f"Pruned! Space reclaimed: {freed} bytes"
                
                return str(data)[:500]
            except json.JSONDecodeError:
                return f"Response: {body.decode()[:500]}"
        
        return "Error: No response from Docker"
    
    except FileNotFoundError:
        return "Error: Docker socket not found. Make sure Docker is running."
    except ConnectionRefusedError:
        return "Error: Cannot connect to Docker. Check permissions."
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print("Docker plugin loaded. Use 'docker' tool in HelloChusquis.")