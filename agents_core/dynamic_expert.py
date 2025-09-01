"""Dynamic expert agent implementation.

Provides:

- ``ExpertSpec``: a lightweight descriptor of an expert (``expertise``, ``confidence``, ``source``).
- Heuristic mapping from free text to canonical expert categories via ``_EXPERT_SYNONYMS``.
- Optional LLM-aided extraction in ``_llm_experts_from_text()`` that returns an
  ``ExpertSelection`` tuple: ``(experts: list[ExpertSpec], debug: dict)`` where
  ``debug`` contains ``provider``, ``prompt``, ``raw`` and ``parsed`` fields.
- ``select_experts_from_tasks()`` combining heuristics and LLM results with de-duplication
  and a stable category order. Guarantees a fallback generalist when no match is found.
- ``create_agents()`` to instantiate ``DynamicExpertAgent`` instances for each spec.

Notes:
- Cross-domain by design: includes IT and non-IT fields (e.g., legal, finance, marketing,
  operations, healthcare, education). Unknown LLM-returned roles are preserved as-is.
- The LLM provider is detected via ``agents_core.llm.detect_llm()`` unless one is injected.
- Bullet parsing accepts ``-``, ``*``, ``•``, en-dash ``–`` and numbered lists like ``1.``/``1)``.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from .base import BaseAgent
from .llm import LLM, detect_llm


@dataclass(slots=True)
class DynamicExpertAgent(BaseAgent):
    """Cross-functional expert agent spun up on demand."""

    expertise: str = "generalist"

    def solve(self, task: str) -> str:
        """Solve a given task using the agent's expertise and record it."""
        msg = f"[{self.expertise}] solving: {task}"
        self.observe(msg)
        return msg


# --- Dynamic identification of experts ---


@dataclass(slots=True)
class ExpertSpec:
    """Lightweight descriptor for an expert to be created dynamically."""

    expertise: str
    confidence: float = 1.0
    source: str = "heuristic"  # e.g., "heuristic" or "llm"


# Canonical expert categories with simple keyword heuristics
_EXPERT_SYNONYMS: dict[str, tuple[str, ...]] = {
    "frontend": (
        "frontend",
        "ui",
        "ux",
        "react",
        "vue",
        "css",
        "html",
        "javascript",
        "client",
        "bootstrap",
        "tailwind",
        "web ui",
    ),
    "backend": (
        "backend",
        "api",
        "django",
        "fastapi",
        "flask",
        "server",
        "auth",
        "rest",
    ),
    "database": (
        "database",
        "db",
        "sql",
        "postgres",
        "sqlite",
        "mongodb",
        "redis",
        "neo4j",
        "schema",
        "migration",
    ),
    "devops": (
        "deploy",
        "docker",
        "kubernetes",
        "ci",
        "cd",
        "pipeline",
        "github actions",
        "aws",
        "gcp",
        "azure",
        "helm",
        "terraform",
        "prometheus",
        "grafana",
        "nginx",
    ),
    "security": (
        "oauth",
        "jwt",
        "security",
        "sso",
        "vuln",
        "owasp",
        "secrets",
    ),
    "qa": (
        "qa",
        "test",
        "pytest",
        "coverage",
        "unit",
        "integration",
        "selenium",
        "playwright",
        "quality",
    ),
    "ml": (
        "ml",
        "ai",
        "model",
        "transformers",
        "huggingface",
        "langchain",
        "llm",
        "rag",
        "nlp",
    ),
    "product": (
        "product",
        "requirements",
        "acceptance criteria",
        "story",
        "epic",
        "roadmap",
        "backlog",
    ),
    "design": (
        "design",
        "figma",
        "wireframe",
        "prototype",
        "ux",
        "ui",
    ),
    "performance": (
        "performance",
        "perf",
        "load",
        "scalability",
        "benchmark",
        "cache",
    ),
    "realtime": (
        "websocket",
        "channels",
        "socket",
        "realtime",
        "stream",
    ),
    "observability": (
        "logging",
        "monitoring",
        "sentry",
        "tracing",
        "opentelemetry",
    ),
    "knowledge_graph": (
        "neo4j",
        "cypher",
        "graph",
        "ontology",
        "knowledge graph",
    ),
    # --- Non-IT / cross-domain categories ---
    "legal": (
        "legal",
        "law",
        "contract",
        "gdpr",
        "privacy",
        "ip",
        "license",
        "trademark",
        "compliance",
    ),
    "finance": (
        "finance",
        "budget",
        "budgeting",
        "accounting",
        "pricing",
        "cost",
        "roi",
        "revenue",
        "expense",
        "forecast",
        "valuation",
    ),
    "marketing": (
        "marketing",
        "seo",
        "sem",
        "content",
        "campaign",
        "brand",
        "social",
        "advertising",
        "copy",
    ),
    "sales": (
        "sales",
        "crm",
        "pipeline",
        "lead",
        "outreach",
        "negotiation",
        "deal",
    ),
    "hr": (
        "hr",
        "hiring",
        "recruiting",
        "onboarding",
        "policy",
        "payroll",
        "benefits",
        "people",
    ),
    "operations": (
        "operations",
        "process",
        "supply",
        "logistics",
        "procurement",
        "vendor",
        "inventory",
        "ops",
    ),
    "governance": (
        "governance",
        "risk",
        "audit",
        "gxp",
        "sox",
        "gxp compliance",
    ),
    "healthcare": (
        "healthcare",
        "medical",
        "clinical",
        "patient",
        "diagnosis",
        "treatment",
        "hipaa",
        "fda",
    ),
    "education": (
        "education",
        "teaching",
        "curriculum",
        "training",
        "learning",
        "pedagogy",
    ),
    "research": (
        "research",
        "experiment",
        "hypothesis",
        "analysis",
        "survey",
        "literature",
    ),
    "data_science": (
        "data science",
        "analytics",
        "statistics",
        "modeling",
        "visualization",
        "hypothesis testing",
    ),
    "ethics": (
        "ethics",
        "fairness",
        "bias",
        "responsible ai",
    ),
    "localization": (
        "localization",
        "translation",
        "i18n",
        "l10n",
    ),
    "manufacturing": (
        "manufacturing",
        "production",
        "quality control",
        "lean",
        "six sigma",
    ),
    "support": (
        "support",
        "customer support",
        "helpdesk",
        "ticket",
        "csat",
    ),
}


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


# Type aliases for concise annotations
ExpertDebug = dict[str, object]
ExpertSelection = tuple[list[ExpertSpec], ExpertDebug]


def _heuristic_experts_from_text(text: str) -> list[ExpertSpec]:
    """Return a list of ExpertSpec inferred from free text using keywords."""
    t = _normalize(text)
    found: list[ExpertSpec] = []
    for category, words in _EXPERT_SYNONYMS.items():
        if any(w in t for w in words):
            found.append(ExpertSpec(expertise=category, confidence=0.7, source="heuristic"))
    return found


def _parse_bulleted_lines(text: str) -> list[str]:
    """Parse bullet-like lines ("- x", "* x", "• x", "1. x", "1) x")."""
    pattern = r"^\s*(?:\\?[-*•–]|\d+[\.)])\s+(.*)$"
    out: list[str] = []
    for line in (text or "").splitlines():
        m = re.match(pattern, line.strip())
        if m:
            out.append(m.group(1).strip())
    return out


def _catalog_string() -> str:
    """Return a comma-separated catalog of canonical expert roles."""
    return ", ".join(_EXPERT_SYNONYMS.keys())


def _build_crossdomain_prompt(text: str) -> str:
    """Construct the LLM prompt for cross-domain expert extraction."""
    catalog = _catalog_string()
    return (
        "You coordinate a cross-domain expert team (IT and non-IT). "
        "From the tasks/description, list the required expert roles as bullet lines "
        "starting with '- '. Prefer canonical roles from this catalog when applicable: "
        f"{catalog}. If a suitable role is not in the catalog, output a precise freeform role.\n"
        f"Input:\n{text}\n"
        "Return only the list of roles, one per line, no extra text."
    )


def _map_role_to_spec(role_norm: str) -> ExpertSpec | None:
    """Map a normalized role string to a canonical ExpertSpec if possible.

    Returns None when no canonical mapping is found.
    """
    if role_norm in _EXPERT_SYNONYMS:
        return ExpertSpec(expertise=role_norm, confidence=0.9, source="llm")
    for cat, words in _EXPERT_SYNONYMS.items():
        if (
            role_norm == cat
            or any(role_norm == w for w in words)
            or any(role_norm in w for w in words)
        ):
            return ExpertSpec(expertise=cat, confidence=0.6, source="llm")
    return None


def _llm_experts_from_text(text: str, llm: LLM | None = None) -> ExpertSelection:
    """Ask an LLM to propose expert roles; parse and map to canonical categories."""
    provider = llm if llm is not None else detect_llm()
    debug: ExpertDebug = {
        "provider": provider.__class__.__name__ if provider else None,
        "prompt": None,
        "raw": None,
        "parsed": [],
    }
    if provider is None:
        return [], debug
    prompt = _build_crossdomain_prompt(text)
    debug["prompt"] = prompt
    try:
        raw = provider.generate(prompt)
        debug["raw"] = raw
        roles = _parse_bulleted_lines(raw)
        debug["parsed"] = roles
    except RuntimeError:
        return [], debug

    mapped: list[ExpertSpec] = []
    for r in roles:
        r_norm = _normalize(r)
        spec = _map_role_to_spec(r_norm)
        if spec is None and r_norm:
            # preserve unknown roles as-is to enable non-IT experts
            spec = ExpertSpec(expertise=r_norm, confidence=0.5, source="llm")
        if spec is not None:
            mapped.append(spec)
    # de-duplicate by expertise, keep highest confidence
    best: dict[str, ExpertSpec] = {}
    for spec in mapped:
        cur = best.get(spec.expertise)
        if cur is None or spec.confidence > cur.confidence:
            best[spec.expertise] = spec
    return list(best.values()), debug


def select_experts_from_tasks(tasks: Iterable[str], llm: LLM | None = None) -> ExpertSelection:
    """Identify a set of experts needed for the given tasks.

    Combines heuristic keyword matching with optional LLM-driven extraction, then
    de-duplicates and returns a stable-ordered list. Guarantees at least one
    generalist if no matches are found.
    """
    text = "\n".join(tasks)
    heur = _heuristic_experts_from_text(text)
    llm_specs, llm_dbg = _llm_experts_from_text(text, llm=llm)
    combined: dict[str, ExpertSpec] = {s.expertise: s for s in heur}
    for s in llm_specs:
        cur = combined.get(s.expertise)
        if cur is None or s.confidence > cur.confidence:
            combined[s.expertise] = s
    # Stable order by a predefined ranking based on _EXPERT_SYNONYMS keys
    rank = {name: idx for idx, name in enumerate(_EXPERT_SYNONYMS.keys())}
    final = sorted(combined.values(), key=lambda s: rank.get(s.expertise, 9999))
    if not final:
        final = [ExpertSpec(expertise="generalist", confidence=0.5, source="fallback")]
    debug = {
        "heuristic": [s.expertise for s in heur],
        "llm": llm_dbg,
        "final": [s.expertise for s in final],
    }
    return final, debug


def create_agents(specs: Iterable[ExpertSpec], *, memory=None) -> list[DynamicExpertAgent]:
    """Instantiate agents for each ExpertSpec."""
    agents: list[DynamicExpertAgent] = []
    for s in specs:
        agents.append(
            DynamicExpertAgent(
                name=f"expert-{s.expertise}",
                role="Expert",
                expertise=s.expertise,
                memory=memory,
            )
        )
    return agents
