"""More built-in functions for HelloChusquis."""

import json
import os
import re
import shlex
import subprocess
import mimetypes
from pathlib import Path
from typing import Any


def get_file_type(path: str) -> dict:
    """Get file type and mime type."""
    p = Path(path)
    if not p.exists():
        return {"error": "File not found"}
    
    suffix = p.suffix.lower()
    mime_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    
    is_text = mime_type.startswith("text/")
    is_image = mime_type.startswith("image/")
    is_audio = mime_type.startswith("audio/")
    is_video = mime_type.startswith("video/")
    
    return {
        "path": path,
        "name": p.name,
        "extension": suffix,
        "mime_type": mime_type,
        "is_text": is_text,
        "is_image": is_image,
        "is_audio": is_audio,
        "is_video": is_video,
        "size": p.stat().st_size
    }


def search_files(directory: str, query: str, extension: str = None) -> dict:
    """Search for files matching query."""
    p = Path(directory)
    if not p.exists():
        return {"error": "Directory not found"}
    
    pattern = f"*{query}*{extension or ''}"
    files = [str(f) for f in p.rglob(pattern)]
    
    return {"files": files[:50], "count": len(files)}


def get_directory_tree(path: str, max_depth: int = 3) -> dict:
    """Get directory tree structure."""
    p = Path(path)
    if not p.exists():
        return {"error": "Directory not found"}
    
    tree = []
    
    def walk(dir_path, depth=0):
        if depth > max_depth:
            return
        try:
            for item in sorted(dir_path.iterdir()):
                tree.append({"path": str(item), "type": "dir" if item.is_dir() else "file", "depth": depth})
                if item.is_dir():
                    walk(item, depth + 1)
        except PermissionError:
            pass
    
    walk(p)
    return {"tree": tree, "count": len(tree)}


def get_disk_usage(path: str = ".") -> dict:
    """Get disk usage information."""
    import shutil
    p = Path(path)
    if not p.exists():
        p = Path(".")
    
    usage = shutil.disk_usage(p)
    total, used, free = usage
    
    return {
        "total": total,
        "used": used,
        "free": free,
        "percent": round(used / total * 100, 2),
        "human": {
            "total": format_size(total),
            "used": format_size(used),
            "free": format_size(free)
        }
    }


def format_size(size: int) -> str:
    """Format file size."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def extract_dates(text: str) -> dict:
    """Extract dates from text."""
    patterns = [
        (r"\d{4}-\d{2}-\d{2}", "YYYY-MM-DD"),
        (r"\d{2}/\d{2}/\d{4}", "MM/DD/YYYY"),
        (r"\d{2}-\d{2}-\d{4}", "DD-MM-YYYY"),
    ]
    
    dates = []
    for pattern, fmt in patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            dates.append({"date": m, "format": fmt})
    
    return {"dates": dates, "count": len(dates)}


def extract_phone_numbers(text: str) -> dict:
    """Extract phone numbers from text."""
    pattern = r"\+?[\d\s\-\(\)]{10,}"
    phones = re.findall(pattern, text)
    cleaned = [re.sub(r"[^\d+]", "", p) for p in phones]
    return {"phones": cleaned, "count": len(cleaned)}


def text_to_json(text: str, delimiter: str = ",") -> dict:
    """Convert text to JSON array."""
    lines = text.strip().split("\n")
    if not lines or not lines[0]:
        return {"error": "No data to parse"}
    if delimiter in lines[0]:
        headers = lines[0].split(delimiter)
        data = []
        for line in lines[1:]:
            if line.strip():
                values = line.split(delimiter)
                obj = dict(zip(headers, values))
                data.append(obj)
        return {"json": json.dumps(data, indent=2), "count": len(data)}
    return {"error": "No delimiter found"}


def json_to_text(json_str: str, delimiter: str = ",") -> str:
    """Convert JSON to text."""
    try:
        data = json.loads(json_str)
        if isinstance(data, list) and data:
            first_item = data[0] if data else {}
            headers = list(first_item.keys()) if first_item else []
            lines = [delimiter.join(headers)]
            for item in data:
                lines.append(delimiter.join(str(item.get(h, "")) for h in headers))
            return {"text": "\n".join(lines), "count": len(data)}
        return {"error": "Invalid JSON array"}
    except Exception as e:
        return {"error": str(e)}


def merge_json(json1: str, json2: str, mode: str = "combine") -> str:
    """Merge two JSON objects or arrays."""
    try:
        d1 = json.loads(json1)
        d2 = json.loads(json2)
        
        if mode == "combine":
            if isinstance(d1, list) and isinstance(d2, list):
                return {"result": json.dumps(d1 + d2)}
            elif isinstance(d1, dict) and isinstance(d2, dict):
                return {"result": json.dumps({**d1, **d2})}
        elif mode == "update":
            if isinstance(d1, dict) and isinstance(d2, dict):
                d1.update(d2)
                return {"result": json.dumps(d1)}
        
        return {"error": "Invalid mode"}
    except Exception as e:
        return {"error": str(e)}


_COMMAND_TIMEOUT_SECONDS = 30
_COMMAND_OUTPUT_MAX_CHARS = 65_536
_COMMAND_ENVIRONMENT_KEYS = ("HOME", "LANG", "LC_ALL", "PATH", "TMPDIR")


def run_command(command: str, shell: bool = False) -> dict:
    """Run a tokenized command without a shell or inherited secrets."""
    if shell:
        return {"error": "shell execution is not supported"}
    if not isinstance(command, str):
        return {"error": "command must be a string"}
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        return {"error": f"invalid command: {exc}"}
    if not argv:
        return {"error": "command cannot be empty"}

    environment = {
        key: value
        for key in _COMMAND_ENVIRONMENT_KEYS
        if (value := os.environ.get(key))
    }
    try:
        result = subprocess.run(
            argv,
            shell=False,
            capture_output=True,
            timeout=_COMMAND_TIMEOUT_SECONDS,
            env=environment,
        )
        stdout = result.stdout.decode("utf-8", errors="replace")[:_COMMAND_OUTPUT_MAX_CHARS]
        stderr = result.stderr.decode("utf-8", errors="replace")[:_COMMAND_OUTPUT_MAX_CHARS]
        return {
            "returncode": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"command timed out after {_COMMAND_TIMEOUT_SECONDS} seconds"}
    except OSError as exc:
        return {"error": f"command failed: {exc}"}


def monitor_process(pid: int) -> dict:
    """Monitor a process."""
    try:
        import psutil
        p = psutil.Process(pid)
        return {
            "pid": pid,
            "name": p.name(),
            "status": p.status(),
            "cpu_percent": p.cpu_percent(),
            "memory_percent": p.memory_percent(),
            "num_threads": p.num_threads(),
            "create_time": p.create_time()
        }
    except Exception as e:
        return {"error": str(e)}


def kill_process(pid: int, force: bool = False) -> dict:
    """Kill a process."""
    try:
        import psutil
        p = psutil.Process(pid)
        p.kill() if force else p.terminate()
        return {"killed": pid, "force": force}
    except Exception as e:
        return {"error": str(e)}


def get_network_interfaces() -> dict:
    """Get network interfaces."""
    try:
        import psutil
        interfaces = psutil.net_if_addrs()
        result = {}
        for name, addrs in interfaces.items():
            result[name] = [{"family": str(a.family), "address": a.address} for a in addrs]
        return result
    except Exception:
        return {"error": "psutil not installed"}


def get_process_list() -> dict:
    """Get list of running processes."""
    try:
        import psutil
        processes = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent"]):
            try:
                processes.append({
                    "pid": p.info["pid"],
                    "name": p.info["name"],
                    "cpu": p.info["cpu_percent"]
                })
            except Exception:
                pass
        return {"processes": processes[:50], "count": len(processes)}
    except Exception:
        return {"error": "psutil not installed"}


def format_json(data: dict, indent: int = 2) -> str:
    """Format JSON with indentation."""
    return {"formatted": json.dumps(data, indent=indent)}


def minify_json(json_str: str) -> str:
    """Minify JSON."""
    try:
        data = json.loads(json_str)
        return {"minified": json.dumps(data, separators=(",", ":"))}
    except Exception as e:
        return {"error": str(e)}


def validate_json(json_str: str) -> dict:
    """Validate JSON string."""
    try:
        data = json.loads(json_str)
        return {"valid": True, "type": type(data).__name__}
    except Exception as e:
        return {"valid": False, "error": str(e)}


def get_json_path(json_str: str, path: str) -> dict:
    """Get value at JSON path."""
    try:
        data = json.loads(json_str)
        keys = path.strip("/").split("/")
        result = data
        for k in keys:
            result = result[k]
        return {"value": result, "path": path}
    except Exception as e:
        return {"error": str(e)}


def set_json_path(json_str: str, path: str, value: Any) -> dict:
    """Set value at JSON path."""
    try:
        data = json.loads(json_str)
        keys = path.strip("/").split("/")
        target = data
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
        return {"result": json.dumps(data), "path": path}
    except Exception as e:
        return {"error": str(e)}