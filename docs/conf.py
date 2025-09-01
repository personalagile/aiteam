from __future__ import annotations

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(".."))

project = "AITEAM"
author = "Aiteam"

# Read version from environment to avoid importing Django at build time
version = os.getenv("AITEAM_VERSION", "0.1.0")
release = version

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinxcontrib.mermaid",
]

# Avoid heavy optional imports during autodoc
autodoc_mock_imports = [
    "channels",
    "channels_redis",
    "celery",
    "neo4j",
    "redis",
    "daphne",
    "langchain",
    "autogen_agentchat",
    "faiss",
    "openai",
    "transformers",
]

# MyST configuration
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "linkify",
]

# Treat fenced code blocks like ```mermaid as a directive for sphinxcontrib-mermaid
myst_fence_as_directive = ["mermaid"]

# Optional: specify mermaid version used by sphinxcontrib-mermaid (rendered client-side)

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "alabaster"
html_static_path = ["_static"]
