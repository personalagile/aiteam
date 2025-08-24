"""Long-term knowledge graph storage using Neo4j (optional dependency).

Provides a minimal interface to upsert notes linked to agents. The module
gracefully degrades when the Neo4j driver is unavailable.
"""

from __future__ import annotations

import os

try:
    from neo4j import GraphDatabase as _GraphDatabase  # type: ignore
    from neo4j.exceptions import Neo4jError as _Neo4jError  # type: ignore
except ImportError:  # pragma: no cover - optional
    _GraphDatabase = None  # type: ignore

    class _Neo4jError(Exception):  # type: ignore
        """Fallback Neo4j error when driver is not installed."""


class KnowledgeGraph:
    """Neo4j-backed knowledge graph (minimal stub)."""

    def __init__(self) -> None:
        self._driver = None
        if _GraphDatabase is None:
            return
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        pwd = os.getenv("NEO4J_PASSWORD")
        if uri and user and pwd:
            try:
                self._driver = _GraphDatabase.driver(uri, auth=(user, pwd))
            except _Neo4jError:  # pragma: no cover - fallback when not available
                self._driver = None

    def upsert_note(self, agent: str, text: str) -> None:
        """Create a note and link it to an agent node if a driver is set."""
        if not self._driver:  # pragma: no cover - noop in dev without neo4j
            return
        query = "MERGE (a:Agent {name:$agent}) CREATE (a)-[:NOTED]->(:Note {text:$text})"
        with self._driver.session() as session:
            session.run(query, agent=agent, text=text)
