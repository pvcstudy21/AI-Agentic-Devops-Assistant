"""Check local prerequisites without installing or changing anything."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from urllib.error import URLError
from urllib.request import urlopen

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from devops_agent.config import OLLAMA_BASE_URL, OLLAMA_MODEL  # noqa: E402


def main() -> int:
    failures = 0
    print(f"Python: {sys.version.split()[0]}")
    if sys.version_info < (3, 11):
        print("  FAIL: Python 3.11 or newer is required.")
        failures += 1
    else:
        print("  OK")

    ollama = shutil.which("ollama")
    print(f"Ollama CLI: {ollama or 'not found'}")
    if not ollama:
        failures += 1
    else:
        subprocess.run([ollama, "--version"], check=False)

    try:
        with urlopen(f"{OLLAMA_BASE_URL}/api/tags", timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
        model_names = [item.get("name", "") for item in payload.get("models", [])]
        print(f"Ollama API: reachable at {OLLAMA_BASE_URL}")
        if any(name == OLLAMA_MODEL or name.startswith(OLLAMA_MODEL + ":") for name in model_names):
            print(f"Configured model: {OLLAMA_MODEL} (available)")
        else:
            print(f"Configured model: {OLLAMA_MODEL} (not found; run: ollama pull {OLLAMA_MODEL})")
            failures += 1
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        print(f"Ollama API: not reachable at {OLLAMA_BASE_URL} ({exc})")
        failures += 1

    kubectl = shutil.which("kubectl")
    print(f"kubectl: {kubectl or 'not found (Kubernetes tool will report unavailable)'}")
    if kubectl:
        subprocess.run([kubectl, "version", "--client"], check=False)

    print(f"\nEnvironment check: {'PASS' if failures == 0 else f'{failures} issue(s) found'}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
