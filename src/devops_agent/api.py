"""Local FastAPI interface for the DevOps agent."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from devops_agent.agent import extract_answer, get_agent


logger = logging.getLogger(__name__)
app = FastAPI(
    title="Agentic DevOps Assistant",
    description="A local-first, read-only, tool-using DevOps assistant.",
    version="0.1.0",
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    thread_id: str = Field(default="default", min_length=1, max_length=100)


class ChatResponse(BaseModel):
    response: str
    thread_id: str


@app.get("/")
def root() -> dict[str, str]:
    return {"application": "Agentic DevOps Assistant", "version": "0.1.0"}


@app.get("/health")
def health() -> dict[str, str]:
    """Report API process health; this does not test Ollama or infrastructure."""
    return {"status": "ok", "application": "agentic-devops-assistant"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        result = get_agent().invoke(
            {"messages": [{"role": "user", "content": request.message}]},
            config={"configurable": {"thread_id": request.thread_id}},
        )
        return ChatResponse(
            response=extract_answer(result),
            thread_id=request.thread_id,
        )
    except Exception as exc:  # noqa: BLE001 - convert runtime failure to an API error.
        logger.exception("Agent request failed")
        raise HTTPException(
            status_code=502,
            detail="Agent execution failed. Check the server terminal for details.",
        ) from exc
