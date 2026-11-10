# Agentic DevOps Assistant

A local-first, read-only DevOps assistant built with **Python, LangChain, LangGraph, Ollama, and FastAPI**.

It can choose and execute Python tools to:

- Check configured HTTP and TCP service endpoints.
- Search local `.log` files and return matching filenames and line numbers.
- Query Kubernetes pods and deployments using read-only `kubectl get` commands.
- Perform multi-step investigations by calling multiple tools and synthesizing their results.
- Keep short-term conversation state per `thread_id` while the process is running.

> **Scope:** This is a learning-oriented V1. It does not restart services, delete pods, change infrastructure, or execute arbitrary shell commands. Sample logs are fictional. Service checks query the endpoints in `config/services.json` on the machine where the assistant runs.

## 1. Architecture

```text
User -> CLI / FastAPI -> LangChain create_agent (LangGraph runtime)
                              |
                              +--> check_service_health -> HTTP/TCP
                              +--> search_logs          -> knowledge/logs/*.log
                              +--> kubernetes_status    -> kubectl get
                              |
                         Ollama chat model
                         InMemorySaver
```

Read [`docs/architecture.md`](docs/architecture.md) and [`docs/learning-guide.md`](docs/learning-guide.md) for the component boundaries and concepts.

## 2. Prerequisites

- Linux, macOS, or Windows with WSL2.
- Python **3.11 or newer**.
- [Ollama](https://ollama.com/download) installed and running.
- A tool-calling-capable Ollama model. The default is `qwen3:4b`.
- Optional: `kubectl` configured for a cluster. Without it, the Kubernetes tool reports that it is unavailable.

The assistant and Ollama are separate processes: Ollama hosts the model; this Python project calls Ollama's local HTTP API.

## 3. Installation (Ubuntu)

Clone your GitHub repository, or extract this project and enter its root directory:

```bash
cd agentic-devops-assistant

python3 --version
python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

cp .env.example .env
```

If your shell blocks activation, use the interpreter directly with `.venv/bin/python` and `.venv/bin/pip`.

## 4. Start Ollama and download the model

In one terminal:

```bash
ollama serve
```

In another terminal:

```bash
ollama pull qwen3:4b
ollama list
```

You can change `OLLAMA_MODEL` in `.env` to another model that supports tool calling. Keep `OLLAMA_BASE_URL` pointed at your local Ollama server.

Check prerequisites:

```bash
python scripts/check_environment.py
```

## 5. Configure services

Edit `config/services.json` to describe endpoints that exist in your environment.

Example:

```json
{
  "api": {
    "type": "http",
    "url": "http://127.0.0.1:8000/health"
  },
  "postgres": {
    "type": "tcp",
    "host": "127.0.0.1",
    "port": 5432
  },
  "redis": {
    "type": "tcp",
    "host": "127.0.0.1",
    "port": 6379
  }
}
```

- HTTP checks request the configured URL and consider a 2xx status healthy.
- TCP checks only establish a TCP connection. They do not authenticate or verify application-level health.
- These are example local endpoints. Change them to match your own services before interpreting results.

## 6. Run the CLI

From the repository root, with the virtual environment active:

```bash
python -m devops_agent.cli
```

Or use the installed command:

```bash
devops-assistant
```

Try these prompts one at a time:

```text
What can you help me with?
Check whether Redis is healthy.
Search the logs for database connection timeout errors.
Show Kubernetes pods in the default namespace.
Investigate why my API is unhealthy. Check its service health and search the logs for errors. Also inspect PostgreSQL logs for related problems.
```

The model decides which tools to call. Exact wording and tool-call order may vary. If a configured service is not running, an unhealthy result is a valid diagnostic result—not necessarily an application bug.

Exit with `exit` or `quit`.

## 7. Run the FastAPI server

```bash
uvicorn devops_agent.api:app --host 127.0.0.1 --port 8000 --reload
```

Open <http://127.0.0.1:8000/docs> for Swagger UI.

Example request to `POST /chat`:

```json
{
  "message": "Search the logs for database timeouts",
  "thread_id": "local-test-001"
}
```

Use the same `thread_id` for follow-up messages in the same running process. Use a different ID for a separate conversation.

`GET /health` only reports whether the FastAPI process responds. It does not check Ollama, the model, or infrastructure services.

## 8. Run tests

```bash
pytest -q
```

The tests cover service configuration handling, a local TCP health check, log search behavior, Kubernetes namespace validation, and the FastAPI request/response contract. They do not require a running Ollama model or Kubernetes cluster.

## 9. Repository structure

```text
agentic-devops-assistant/
├── config/
│   └── services.json             # HTTP/TCP endpoints to check
├── docs/
│   ├── architecture.md           # System boundaries and flow
│   └── learning-guide.md         # Concepts and exercises
├── knowledge/
│   └── logs/
│       ├── api.log               # Fictional sample log
│       ├── postgres.log          # Fictional sample log
│       └── redis.log             # Fictional sample log
├── scripts/
│   └── check_environment.py      # Local prerequisite check
├── src/devops_agent/
│   ├── __init__.py
│   ├── agent.py                  # Model, prompt, agent runtime, memory
│   ├── api.py                    # FastAPI interface
│   ├── cli.py                    # Interactive terminal interface
│   ├── config.py                 # Centralized settings
│   └── tools.py                  # Read-only DevOps tools
├── tests/
│   ├── test_api.py
│   └── test_tools.py
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## 10. Safety and limitations

- **Keep the API local.** It has no authentication. Do not bind it to `0.0.0.0` or expose it to the internet or an untrusted network.
- **Only use trusted service configuration.** The HTTP health-check tool requests URLs specified in `config/services.json`.
- **Kubernetes access follows your kubeconfig.** The tool runs only `kubectl get pods` and `kubectl get deployments`; it does not alter cluster resources.
- **No arbitrary shell tool exists.** The assistant cannot execute arbitrary terminal commands through the supplied tools.
- **Memory is temporary.** `InMemorySaver` stores checkpoints in process memory. Restarting the CLI/server clears them. Use a persistent checkpointer in a later milestone if you need durable conversations.
- **Model output can be wrong.** Verify operational conclusions against the raw tool output before taking action.
- **Sample logs are fictional.** Replace them with approved, sanitized logs when testing against real systems. Never commit secrets or sensitive production logs.

## 11. Troubleshooting

| Symptom | Checks |
|---|---|
| `ModuleNotFoundError: devops_agent` | Activate `.venv`; run `python -m pip install -e ".[dev]"` from repository root. |
| Ollama connection refused | Start Ollama with `ollama serve`; verify `OLLAMA_BASE_URL`. |
| Model not found | Run `ollama pull qwen3:4b`; verify `.env` and `ollama list`. |
| Model answers without using a tool | Confirm the selected model supports tool calling; make the request operational and specific. |
| Health check reports unhealthy | Verify the configured URL/host/port and that the service is actually running. |
| Kubernetes tool says `kubectl` unavailable | Install `kubectl`, configure kubeconfig, and check `kubectl get nodes`. |
| Kubernetes API connection fails | Check `kubectl config current-context` and cluster connectivity. |

## 12. Suggested next milestones

1. Add tool-call tracing and structured logs so each agent action is observable.
2. Replace in-memory checkpointing with SQLite persistence.
3. Build a custom LangGraph `StateGraph` to learn nodes, edges, state, and conditional routing explicitly.
4. Add structured log filters, Docker diagnostics, and richer Kubernetes read-only tools.
5. Add authorization and human approval before introducing any state-changing operation.

## References

- [LangChain agents](https://docs.langchain.com/oss/python/langchain/agents)
- [LangChain tools](https://docs.langchain.com/oss/python/langchain/tools)
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [LangChain Ollama integration](https://reference.langchain.com/python/langchain-ollama)
- [Ollama](https://ollama.com/)
