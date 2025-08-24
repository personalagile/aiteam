"""Pydantic schemas for memory payloads."""

from __future__ import annotations

from pydantic import BaseModel


class MemoryRecord(BaseModel):
    """Schema representing a single memory item for an agent."""

    agent: str
    content: str
