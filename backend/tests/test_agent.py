"""
Tests for the LLM Agent
Run: pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ── API tests ─────────────────────────────────────────────────────────────────
def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_list_tools():
    r = client.get("/tools")
    assert r.status_code == 200
    tools = r.json()["tools"]
    names = [t["name"] for t in tools]
    assert "web_search" in names
    assert "execute_python" in names
    assert "summarize_document" in names
    assert "get_weather" in names
    assert "get_news" in names


def test_ask_empty_question():
    r = client.post("/ask", json={"question": "  ", "session_id": "test"})
    assert r.status_code == 400


def test_upload_invalid_type():
    import io
    r = client.post(
        "/upload",
        files={"file": ("bad.mp4", io.BytesIO(b"data"), "video/mp4")},
    )
    assert r.status_code == 400


# ── Code executor unit tests ──────────────────────────────────────────────────
def test_execute_python_basic():
    from app.tools.code_executor import execute_python
    result = execute_python.invoke("x = 2 + 2\nprint(x)")
    assert "4" in result


def test_execute_python_math():
    from app.tools.code_executor import execute_python
    result = execute_python.invoke("import math\nprint(math.sqrt(144))")
    assert "12" in result


def test_execute_python_blocks_open():
    from app.tools.code_executor import execute_python
    result = execute_python.invoke("open('/etc/passwd', 'r')")
    assert "error" in result.lower() or "not allowed" in result.lower() or "blocked" in result.lower()


def test_execute_python_statistics():
    from app.tools.code_executor import execute_python
    result = execute_python.invoke(
        "import statistics\ndata = [2, 4, 4, 4, 5, 7, 9]\nprint(statistics.mean(data))"
    )
    assert "5" in result


# ── Memory tests ──────────────────────────────────────────────────────────────
def test_memory_isolation():
    from app.agent.react_agent import get_memory, clear_memory
    m1 = get_memory("sess_a")
    m2 = get_memory("sess_b")
    assert m1 is not m2


def test_clear_session():
    r = client.delete("/session/test_session_123")
    assert r.status_code == 200
    assert "cleared" in r.json()["message"]
