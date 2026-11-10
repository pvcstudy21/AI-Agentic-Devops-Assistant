# Learning guide

Use this project to understand the mechanics, not merely to copy working code.

## Concepts mapped to files

| Concept | Implementation | What to inspect |
|---|---|---|
| Tool | `tools.py` | `@tool`, function docstrings, input schemas |
| Tool registry | `tools.py` | `DEVOPS_TOOLS` |
| Model integration | `agent.py` | `ChatOllama` |
| Agent loop | `agent.py` | `create_agent` runtime and tool-result cycle |
| Harness / orchestration | `agent.py`, `cli.py`, `api.py` | Model, prompts, tools, state, interfaces and errors |
| Context engineering | `agent.py` | `SYSTEM_PROMPT` and retrieved tool results |
| Short-term memory | `agent.py` | `InMemorySaver` |
| Conversation/thread identity | `cli.py`, `api.py` | `thread_id` |
| External process integration | `tools.py` | `subprocess.run` with argument lists |
| API schema validation | `api.py` | Pydantic request and response models |

## Suggested experiments

1. Ask for a health check and observe whether the model selects the health tool.
2. Ask for an exact log phrase and compare the answer with `grep -in` output.
3. Ask a question that needs both API health and logs; observe the sequence of tool calls.
4. Ask a follow-up using the same thread ID, then use a new thread ID and compare memory behavior.
5. Temporarily stop Ollama and observe how the application reports the failure.
6. Change a service port in `config/services.json` and see how configuration changes behavior without editing Python.
7. Inspect `kubernetes_status` and identify why namespace validation and read-only commands matter.

## Important distinction

The model does not directly execute Python or `kubectl`. It requests a tool call using the tool schema. The LangChain runtime dispatches the call to Python, receives the result, and gives that result back to the model so it can continue or answer.
