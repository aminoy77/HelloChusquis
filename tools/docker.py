"""Safe Docker daemon integration over a local Unix socket only."""

from __future__ import annotations

import asyncio
import os
import re
import stat
from typing import Any

import httpx


_DOCKER_BASE_URL = "http://docker"
_CONTAINER_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")
_IMAGE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/@:-]{0,511}")


def _docker_socket() -> str:
    """Require a local Unix-domain Docker socket instead of an unauthenticated TCP daemon."""
    socket_path = os.getenv("DOCKER_SOCKET", "/var/run/docker.sock")
    try:
        metadata = os.stat(socket_path)
    except OSError as exc:
        raise ValueError(f"Docker socket is unavailable: {socket_path}") from exc
    if not stat.S_ISSOCK(metadata.st_mode):
        raise ValueError("DOCKER_SOCKET must reference a Unix-domain socket.")
    if metadata.st_mode & stat.S_IWOTH:
        raise ValueError("Docker socket must not be world-writable.")
    return socket_path


def _container_id(value: object) -> str:
    """Validate a container identifier or name before embedding it in a daemon route."""
    identifier = str(value or "").strip()
    if not _CONTAINER_ID_RE.fullmatch(identifier):
        raise ValueError("container_id must be a single safe path segment.")
    return identifier


def _image_ref(value: object) -> str:
    """Validate a Docker image reference before it is sent to the local daemon."""
    image = str(value or "").strip()
    if not _IMAGE_RE.fullmatch(image) or ".." in image.split("/"):
        raise ValueError("image must be a non-empty, safe Docker image reference.")
    return image


def _container_name(value: object) -> str | None:
    name = str(value or "").strip()
    if not name:
        return None
    if not _CONTAINER_ID_RE.fullmatch(name):
        raise ValueError("name must be a single safe Docker container name.")
    return name


def _payload(response: httpx.Response) -> dict[str, Any]:
    if not response.content:
        return {"status": response.status_code, "success": response.is_success}
    try:
        body = response.json()
    except ValueError:
        body = {"text": response.text[:2000]}
    return body if isinstance(body, dict) else {"data": body}


async def _async_request(
    method: str,
    path: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    transport = httpx.AsyncHTTPTransport(uds=_docker_socket())
    async with httpx.AsyncClient(
        transport=transport,
        base_url=_DOCKER_BASE_URL,
        timeout=30,
        follow_redirects=False,
    ) as client:
        response = await client.request(method, path, json=json, params=params)
        return _payload(response)


def _sync_request(
    method: str,
    path: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    transport = httpx.HTTPTransport(uds=_docker_socket())
    with httpx.Client(
        transport=transport,
        base_url=_DOCKER_BASE_URL,
        timeout=30,
        follow_redirects=False,
    ) as client:
        response = client.request(method, path, json=json, params=params)
        return _payload(response)


async def list_containers(api_key: str = "") -> dict[str, Any]:
    """List containers via the local Unix socket; TCP Docker endpoints are never used."""
    del api_key
    return await _async_request("GET", "/containers/json")


async def create_container(image: str, name: str, api_key: str = "") -> dict[str, Any]:
    """Create a container from a validated image reference and optional container name."""
    del api_key
    container_name = _container_name(name)
    params = {"name": container_name} if container_name else None
    return await _async_request("POST", "/containers/create", json={"Image": _image_ref(image)}, params=params)


async def start_container(container_id: str, api_key: str = "") -> dict[str, Any]:
    """Start a container selected by a validated identifier."""
    del api_key
    return await _async_request("POST", f"/containers/{_container_id(container_id)}/start")


async def stop_container(container_id: str, api_key: str = "") -> dict[str, Any]:
    """Stop a container selected by a validated identifier."""
    del api_key
    return await _async_request("POST", f"/containers/{_container_id(container_id)}/stop")


async def remove_container(container_id: str, api_key: str = "") -> dict[str, Any]:
    """Remove a container selected by a validated identifier."""
    del api_key
    return await _async_request("DELETE", f"/containers/{_container_id(container_id)}")


def run(action: str, **kwargs: Any) -> str:
    """Synchronous dispatcher for Docker operations guarded by approval policy upstream."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, kwargs)
        return loop.run_until_complete(_run_async(action, kwargs))
    except RuntimeError:
        return _run_sync(action, kwargs)


async def _run_async(action: str, kwargs: dict[str, Any]) -> str:
    if action == "list_containers":
        result = await list_containers()
    elif action == "create_container":
        result = await create_container(kwargs.get("image", ""), kwargs.get("name", ""))
    elif action == "start_container":
        result = await start_container(kwargs.get("container_id", ""))
    elif action == "stop_container":
        result = await stop_container(kwargs.get("container_id", ""))
    elif action == "remove_container":
        result = await remove_container(kwargs.get("container_id", ""))
    else:
        return "Error: Unknown action '{}'. Available: list_containers, create_container, start_container, stop_container, remove_container".format(action)
    return str(result)[:2000]


def _run_sync(action: str, kwargs: dict[str, Any]) -> str:
    try:
        if action == "list_containers":
            result = _sync_request("GET", "/containers/json")
        elif action == "create_container":
            name = _container_name(kwargs.get("name", ""))
            result = _sync_request(
                "POST",
                "/containers/create",
                json={"Image": _image_ref(kwargs.get("image", ""))},
                params={"name": name} if name else None,
            )
        elif action == "start_container":
            result = _sync_request("POST", f"/containers/{_container_id(kwargs.get('container_id', ''))}/start")
        elif action == "stop_container":
            result = _sync_request("POST", f"/containers/{_container_id(kwargs.get('container_id', ''))}/stop")
        elif action == "remove_container":
            result = _sync_request("DELETE", f"/containers/{_container_id(kwargs.get('container_id', ''))}")
        else:
            return "Error: Unknown action '{}'. Available: list_containers, create_container, start_container, stop_container, remove_container".format(action)
        return str(result)[:2000]
    except (httpx.HTTPError, ValueError) as exc:
        return f"Error: {exc}"
