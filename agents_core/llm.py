"""Lightweight, optional LLM providers with safe fallbacks.

This module avoids hard dependencies: it tries providers only when the
corresponding environment variables or libraries are present, otherwise it
falls back to a no-op EchoLLM. Intended for local dev and CI without
network/LMMs.
"""

from __future__ import annotations

import importlib
import os
from dataclasses import dataclass
from typing import Protocol

import requests
import structlog


class LLM(Protocol):
    """Protocol for minimal LLM interface used by agents."""

    def generate(self, prompt: str) -> str:  # pragma: no cover - thin wrapper
        """Generate a completion for the given prompt."""
        raise NotImplementedError


@dataclass(slots=True)
class EchoLLM:
    """Deterministic fallback that echoes the prompt."""

    prefix: str = ""

    def generate(self, prompt: str) -> str:  # pragma: no cover - trivial
        """Return the prompt unchanged, or with a prefix if configured."""
        logger = structlog.get_logger(__name__)
        logger.debug("llm.request", provider="echo", prompt=prompt)
        out = f"{self.prefix}{prompt}" if self.prefix else prompt
        logger.debug("llm.response", provider="echo", response=out)
        return out


@dataclass(slots=True)
class OllamaLLM:
    """Ollama HTTP API client.

    Requires OLLAMA_HOST and optionally OLLAMA_MODEL.
    """

    host: str
    model: str = "llama3.1:8b"
    timeout: int = 20

    def generate(self, prompt: str) -> str:
        """Call the Ollama HTTP API to generate text for the prompt."""
        url = self.host.rstrip("/") + "/api/generate"
        logger = structlog.get_logger(__name__)
        logger.debug(
            "llm.request",
            provider="ollama",
            url=url,
            model=self.model,
            prompt=prompt,
        )
        try:
            resp = requests.post(
                url,
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            text = (data.get("response") or "").strip()
            logger.debug("llm.response", provider="ollama", model=self.model, response=text)
            return text
        except requests.RequestException as exc:  # pragma: no cover - network
            raise RuntimeError("ollama request failed") from exc
        except ValueError as exc:  # pragma: no cover - json
            raise RuntimeError("ollama bad response") from exc


@dataclass(slots=True)
class OpenAILLM:
    """OpenAI Chat API client using the v1 python SDK.

    Requires OPENAI_API_KEY. Model via OPENAI_MODEL (default gpt-4o-mini).
    """

    model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def generate(self, prompt: str) -> str:  # pragma: no cover - external
        """Generate a response using the OpenAI Chat Completions API."""
        try:
            openai_mod = importlib.import_module("openai")  # type: ignore
        except Exception as exc:  # pragma: no cover  # pylint: disable=broad-exception-caught
            raise RuntimeError("openai SDK not available") from exc
        try:
            client = openai_mod.OpenAI()
            logger = structlog.get_logger(__name__)
            logger.debug("llm.request", provider="openai", model=self.model, prompt=prompt)
            res = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful agile software assistant.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=300,
            )
            text = (res.choices[0].message.content or "").strip()
            logger.debug("llm.response", provider="openai", model=self.model, response=text)
            return text
        except Exception as exc:  # pragma: no cover  # pylint: disable=broad-exception-caught
            raise RuntimeError("openai request failed") from exc


@dataclass(slots=True)
class TransformersLLM:
    """Local Transformers pipeline if available.

    Requires TRANSFORMERS_MODEL, will try to instantiate a text-generation
    pipeline. Slow and heavy; for local experimentation.
    """

    model: str
    max_new_tokens: int = 256

    def __post_init__(self) -> None:  # pragma: no cover - optional
        """Lazily import transformers and create a text-generation pipeline."""
        try:
            transformers_mod = importlib.import_module("transformers")  # type: ignore
        except Exception as exc:  # pragma: no cover  # pylint: disable=broad-exception-caught
            raise RuntimeError("transformers not available") from exc
        self._pipe = transformers_mod.pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.model,
            max_new_tokens=self.max_new_tokens,
        )

    def generate(self, prompt: str) -> str:  # pragma: no cover - optional
        """Generate text locally using the transformers pipeline."""
        logger = structlog.get_logger(__name__)
        logger.debug("llm.request", provider="transformers", model=self.model, prompt=prompt)
        try:
            out = self._pipe(prompt)
            text = out[0]["generated_text"]
            text = text.strip()
            logger.debug("llm.response", provider="transformers", model=self.model, response=text)
            return text
        except Exception as exc:  # pragma: no cover  # pylint: disable=broad-exception-caught
            raise RuntimeError("transformers generation failed") from exc


def _env_truthy(name: str, default: str = "0") -> bool:
    val = os.getenv(name, default).strip().lower()
    return val in {"1", "true", "yes", "on"}


def detect_llm() -> LLM | None:
    """Detect and create an LLM provider if explicitly enabled.

    Order: OPENAI -> OLLAMA -> TRANSFORMERS. Returns None if disabled or
    provider cannot be initialized.
    """
    if not _env_truthy("ENABLE_LLM", "0"):
        return None

    # OpenAI
    if os.getenv("OPENAI_API_KEY"):
        try:
            return OpenAILLM()
        except Exception:  # pragma: no cover  # pylint: disable=broad-exception-caught
            pass

    # Ollama
    host = os.getenv("OLLAMA_HOST")
    if host:
        try:
            return OllamaLLM(host=host, model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"))
        except Exception:  # pragma: no cover  # pylint: disable=broad-exception-caught
            pass

    # Transformers
    model = os.getenv("TRANSFORMERS_MODEL")
    if model:
        try:
            return TransformersLLM(model=model)
        except Exception:  # pragma: no cover  # pylint: disable=broad-exception-caught
            pass

    # Last resort
    return EchoLLM(prefix="[echo] ")
