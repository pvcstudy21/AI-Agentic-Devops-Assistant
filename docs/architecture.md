# Architecture

```text
User
  |
  v
CLI or FastAPI
  |
  v
LangChain create_agent (agent runtime backed by LangGraph)
  |                     ^
  | tool call            | tool result
  v                     |
Python tools ------------
  |-- check_service_health -> HTTP/TCP checks from config/services.json
  |-- search_logs          -> knowledge/logs/*.log
  `-- kubernetes_status    -> read-only kubectl get commands

LangGraph InMemorySaver stores conversation state by thread_id in this process.
Ollama hosts the local chat model (default: qwen3:4b).
```

## Boundaries

- The LLM chooses whether to call an available tool; Python performs the actual operation.
- The tools in V1 are read-only. They do not restart services, edit files, or mutate Kubernetes resources.
- The service checks and log files are local to the machine running the assistant.
- `InMemorySaver` is ephemeral. Restarting the process clears conversation checkpoints.
- The API has no authentication in V1 and must stay on localhost.
