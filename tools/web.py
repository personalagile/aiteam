"""Lightweight web utility functions (fetch + parse HTML to text)."""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup


def fetch_url(url: str, timeout: int = 20) -> str:
    """Fetch a URL and return visible text content (best-effort)."""
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    content_type: str | None = resp.headers.get("content-type")
    if content_type and "html" in content_type:
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)
    return resp.text
