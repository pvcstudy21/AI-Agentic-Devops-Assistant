from __future__ import annotations

import json

from devops_agent import tools


def test_unknown_service_lists_available_services(tmp_path, monkeypatch):
    config_path = tmp_path / "services.json"
    config_path.write_text(json.dumps({"redis": {"type": "tcp", "host": "127.0.0.1", "port": 6379}}))
    monkeypatch.setattr(tools, "SERVICES_CONFIG", config_path)

    result = tools.check_service_health.invoke({"service_name": "unknown"})

    assert "Unknown service" in result
    assert "redis" in result


def test_tcp_health_check_against_open_local_port(tmp_path, monkeypatch):
    import socket

    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    host, port = listener.getsockname()
    config_path = tmp_path / "services.json"
    config_path.write_text(json.dumps({"test-service": {"type": "tcp", "host": host, "port": port}}))
    monkeypatch.setattr(tools, "SERVICES_CONFIG", config_path)
    try:
        result = tools.check_service_health.invoke({"service_name": "test-service"})
        assert "HEALTHY" in result
    finally:
        listener.close()


def test_search_logs_returns_filename_and_line_number(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "api.log").write_text("INFO service started\nERROR Database timeout\n")
    (log_dir / "redis.log").write_text("INFO ready\n")
    monkeypatch.setattr(tools, "KNOWLEDGE_DIR", tmp_path)

    result = tools.search_logs.invoke({"query": "database timeout"})

    assert "api.log:2:" in result
    assert "ERROR Database timeout" in result


def test_search_logs_is_case_insensitive(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "api.log").write_text("ERROR DATABASE TIMEOUT\n")
    monkeypatch.setattr(tools, "KNOWLEDGE_DIR", tmp_path)

    result = tools.search_logs.invoke({"query": "database timeout"})

    assert "Found 1 matching" in result


def test_search_logs_rejects_empty_query():
    result = tools.search_logs.invoke({"query": "   "})
    assert "cannot be empty" in result


def test_search_logs_rejects_out_of_range_limit():
    result = tools.search_logs.invoke({"query": "ERROR", "limit": 101})
    assert "between 1 and 100" in result


def test_kubernetes_rejects_invalid_namespace_before_running_command():
    result = tools.kubernetes_status.invoke({"namespace": "default;whoami"})
    assert "Invalid namespace" in result
