"""Centralized configuration for the assistant."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _resolve_project_path(value: str) -> Path:
    """Resolve an absolute path as-is, or a relative path from the repo root."""
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve()


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")
KNOWLEDGE_DIR = _resolve_project_path(os.getenv("KNOWLEDGE_DIR", "knowledge"))
SERVICES_CONFIG = _resolve_project_path(
    os.getenv("SERVICES_CONFIG", "config/services.json")
)

try:
    TOOL_TIMEOUT_SECONDS = max(1, min(30, int(os.getenv("TOOL_TIMEOUT_SECONDS", "5"))))
except ValueError:
    TOOL_TIMEOUT_SECONDS = 5
