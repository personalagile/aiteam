from __future__ import annotations

from typing import Any

import pytest

from agents_core.llm import EchoLLM, OllamaLLM, detect_llm
from agents_core.product_owner import ProductOwnerAgent
from memory.schemas import MemoryRecord
from orchestrator.tasks import run_retro
from tools.search import web_search
from tools.web import fetch_url


def test_detect_llm_echo_when_enabled_without_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENABLE_LLM", "1")
    for k in ("OPENAI_API_KEY", "OLLAMA_HOST", "TRANSFORMERS_MODEL"):
        monkeypatch.delenv(k, raising=False)
    provider = detect_llm()
    assert isinstance(provider, EchoLLM)
    assert provider.generate("hello").startswith("[echo] ")


def test_ollama_generate_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Resp:
        def __init__(self) -> None:
            self._json = {"response": " hi there  "}
            self.headers = {"content-type": "application/json"}

        def raise_for_status(self) -> None:  # noqa: D401 - stub
            return None

        def json(self) -> dict[str, Any]:
            return self._json

    def _post(url: str, json: dict[str, Any], timeout: int) -> Any:  # noqa: A002 - param name
        return _Resp()

    import requests as _requests

    monkeypatch.setattr(_requests, "post", _post, raising=True)
    llm = OllamaLLM(host="http://localhost:11434", model="llama3.1:8b")
    out = llm.generate("hello")
    assert out == "hi there"


def test_product_owner_parses_llm_bullets(monkeypatch: pytest.MonkeyPatch) -> None:
    class _MockLLM:
        def generate(self, prompt: str) -> str:  # noqa: D401 - stub
            return "- Task A\n- Task B\n- Task C"

    po = ProductOwnerAgent(name="po", role="Product Owner", memory=None, llm=_MockLLM())
    tasks = po.plan_work("Build chat")
    assert tasks == ["Task A", "Task B", "Task C"]


def test_web_search_stub() -> None:
    results = web_search("test", k=3)
    assert isinstance(results, list) and results and "test" in results[0]


def test_fetch_url_parses_html(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Resp:
        status_code = 200
        headers = {"content-type": "text/html; charset=utf-8"}
        text = (
            "<html><head><style>.x{}</style><script>1+1</script></head>"
            "<body><h1>Title</h1><p>Hello</p></body></html>"
        )

        def raise_for_status(self) -> None:  # noqa: D401 - stub
            return None

    import requests as _requests

    monkeypatch.setattr(_requests, "get", lambda url, timeout=20: _Resp(), raising=True)
    text = fetch_url("http://example.com")
    assert "Title" in text and "Hello" in text and "1+1" not in text


def test_fetch_url_plain_text(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Resp:
        status_code = 200
        headers = {"content-type": "text/plain"}
        text = "plain content"

        def raise_for_status(self) -> None:  # noqa: D401 - stub
            return None

    import requests as _requests

    monkeypatch.setattr(_requests, "get", lambda url, timeout=20: _Resp(), raising=True)
    text = fetch_url("http://example.com")
    assert text == "plain content"


def test_wsgi_import_executes_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ensure DJANGO_SETTINGS_MODULE is set for import side-effects
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "aiteam.settings")
    import importlib

    mod = importlib.import_module("aiteam.wsgi")
    assert hasattr(mod, "application")


def test_orchestrator_run_retro_returns_ok() -> None:
    assert run_retro() == "ok"


def test_memory_record_schema() -> None:
    rec = MemoryRecord(agent="po", content="foo")
    assert rec.agent == "po" and rec.content == "foo"


def test_short_term_memory_with_fake_client(monkeypatch: pytest.MonkeyPatch) -> None:
    from memory.short_term import ShortTermMemory

    class _FakeClient:
        def __init__(self) -> None:
            self.store: dict[str, list[str]] = {}

        def ping(self) -> None:  # noqa: D401 - stub
            return None

        def rpush(self, key: str, value: str) -> None:
            self.store.setdefault(key, []).append(value)

        def lrange(self, key: str, start: int, end: int) -> list[str]:
            data = self.store.get(key, [])
            n = len(data)
            if n == 0:
                return []
            # Emulate Redis: negative indices are offsets from the end
            if start < 0:
                start = n + start
            if end < 0:
                end = n + end
            start = max(start, 0)
            end = min(end, n - 1)
            if start > end:
                return []
            return data[start : end + 1]

    stm = ShortTermMemory()
    # Force use of the fake redis client to exercise the redis code paths
    stm._client = _FakeClient()  # type: ignore[attr-defined]
    stm.append("po", "x")
    hist = stm.history("po", limit=1)
    assert hist == ["x"]
