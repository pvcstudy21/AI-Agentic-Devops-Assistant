"""Read-only operational tools exposed to the LLM."""

from __future__ import annotations

import json
import re
import shutil
import socket
import subprocess
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from langchain.tools import tool

from devops_agent.config import (
    KNOWLEDGE_DIR,
    SERVICES_CONFIG,
    TOOL_TIMEOUT_SECONDS,
)


_NAMESPACE_PATTERN = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$")


def _load_services() -> dict:
    """Read and validate the local service registry."""
    try:
        with SERVICES_CONFIG.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        raise RuntimeError(f"Service configuration not found: {SERVICES_CONFIG}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in {SERVICES_CONFIG}: {exc}") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Service configuration must contain a JSON object.")
    return data


@tool
def check_service_health(service_name: str) -> str:
    """Check one configured HTTP or TCP service by its name (for example api, postgres, or redis)."""
    name = service_name.strip().lower()
    if not name:
        return "Service name cannot be empty."

    try:
        services = _load_services()
    except RuntimeError as exc:
        return f"Configuration error: {exc}"

    if name not in services:
        available = ", ".join(sorted(services)) or "none"
        return f"Unknown service '{name}'. Available services: {available}."

    service = services[name]
    if not isinstance(service, dict):
        return f"Invalid configuration for service '{name}'."

    service_type = service.get("type")

    if service_type == "http":
        url = service.get("url")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            return f"Invalid HTTP URL configured for service '{name}'."
        try:
            with urlopen(url, timeout=TOOL_TIMEOUT_SECONDS) as response:
                status = response.status
                health = "HEALTHY" if 200 <= status < 300 else "UNHEALTHY"
                return f"Service: {name}\nType: HTTP\nHTTP status: {status}\nHealth: {health}"
        except HTTPError as exc:
            return (
                f"Service: {name}\nType: HTTP\nHTTP status: {exc.code}\n"
                f"Health: UNHEALTHY\nError: {exc.reason}"
            )
        except (URLError, TimeoutError, OSError) as exc:
            return f"Service: {name}\nType: HTTP\nHealth: UNHEALTHY\nError: {exc}"

    if service_type == "tcp":
        host = service.get("host")
        port = service.get("port")
        if not isinstance(host, str) or not host.strip():
            return f"Invalid TCP host configured for service '{name}'."
        if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
            return f"Invalid TCP port configured for service '{name}'."
        try:
            with socket.create_connection((host, port), timeout=TOOL_TIMEOUT_SECONDS):
                return (
                    f"Service: {name}\nType: TCP\nEndpoint: {host}:{port}\n"
                    "Health: HEALTHY (TCP connection succeeded)."
                )
        except OSError as exc:
            return (
                f"Service: {name}\nType: TCP\nEndpoint: {host}:{port}\n"
                f"Health: UNHEALTHY\nError: {exc}"
            )

    return f"Unsupported service type '{service_type}' for service '{name}'."


@tool
def search_logs(query: str, limit: int = 20) -> str:
    """Search local .log files for a literal keyword or phrase; include matching file names and line numbers."""
    search_term = query.strip()
    if not search_term:
        return "Search query cannot be empty."
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        return "Limit must be an integer between 1 and 100."

    log_directory = (KNOWLEDGE_DIR / "logs").resolve()
    if not log_directory.is_dir():
        return f"Log directory does not exist: {log_directory}"

    matches: list[str] = []
    read_errors: list[str] = []

    for log_file in sorted(log_directory.glob("*.log")):
        if not log_file.is_file():
            continue
        try:
            with log_file.open("r", encoding="utf-8", errors="replace") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if search_term.casefold() in line.casefold():
                        matches.append(f"{log_file.name}:{line_number}: {line.rstrip()}")
                        if len(matches) >= limit:
                            break
        except OSError as exc:
            read_errors.append(f"{log_file.name}: {exc}")
        if len(matches) >= limit:
            break

    if not matches:
        result = f"No log entries found for query: {search_term!r}."
    else:
        result = f"Found {len(matches)} matching log entr{'y' if len(matches) == 1 else 'ies'}:\n"
        result += "\n".join(matches)

    if read_errors:
        result += "\n\nFiles that could not be read:\n" + "\n".join(read_errors)
    return result


@tool
def kubernetes_status(namespace: str = "default") -> str:
    """Show Kubernetes pods and deployments in a namespace using read-only kubectl get commands."""
    namespace = namespace.strip()
    if not _NAMESPACE_PATTERN.fullmatch(namespace):
        return "Invalid namespace. Use a lowercase Kubernetes namespace name."

    kubectl = shutil.which("kubectl")
    if kubectl is None:
        return "kubectl is not installed or is not available in PATH."

    commands = [
        [kubectl, "get", "pods", "-n", namespace, "-o", "wide"],
        [kubectl, "get", "deployments", "-n", namespace],
    ]
    outputs: list[str] = []

    for command in commands:
        label = " ".join(command)
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
        except subprocess.TimeoutExpired:
            outputs.append(f"$ {label}\nCommand timed out after 15 seconds.")
            continue
        except OSError as exc:
            outputs.append(f"$ {label}\nCould not execute kubectl: {exc}")
            continue

        output = completed.stdout.strip() or completed.stderr.strip() or "(no output)"
        if len(output) > 12000:
            output = output[:12000] + "\n...[output truncated]"
        outputs.append(f"$ {label}\nExit code: {completed.returncode}\n{output}")

    return "Kubernetes read-only status results:\n\n" + "\n\n".join(outputs)


DEVOPS_TOOLS = [
    check_service_health,
    search_logs,
    kubernetes_status,
]
