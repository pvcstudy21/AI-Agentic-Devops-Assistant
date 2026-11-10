"""Interactive terminal interface."""

from __future__ import annotations

import argparse
import logging
from uuid import uuid4

from devops_agent.agent import extract_answer, get_agent


logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


def run_chat(thread_id: str) -> None:
    agent = get_agent()
    config = {"configurable": {"thread_id": thread_id}}

    print("\n=======================================")
    print("       AGENTIC DEVOPS ASSISTANT")
    print("=======================================")
    print(f"Thread ID: {thread_id}")
    print("Type 'exit' or 'quit' to finish.\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if question.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        if not question:
            continue

        try:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": question}]},
                config=config,
            )
            print(f"\nAssistant: {extract_answer(result)}\n")
        except Exception as exc:  # noqa: BLE001 - CLI must keep the session usable.
            logging.exception("Agent execution failed")
            print(f"\nAgent error: {exc}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Chat with the local DevOps agent.")
    parser.add_argument(
        "--thread-id",
        default=None,
        help="Reuse a thread ID within this running process (defaults to a new UUID).",
    )
    args = parser.parse_args()
    run_chat(args.thread_id or str(uuid4()))


if __name__ == "__main__":
    main()
