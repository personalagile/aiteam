# Security Policy

## Supported Versions

We currently support the latest `main` branch. For releases, we follow Semantic Versioning.

## Reporting a Vulnerability

- Preferred: Open a GitHub Security Advisory for this repository (private to maintainers).
- If advisories are unavailable: Open a new issue titled "Security disclosure request" without sensitive details; a maintainer will contact you to coordinate a private channel.

Please include:
- Affected versions/commit
- Environment details (OS, Python, services)
- Steps to reproduce
- Potential impact

We strive to acknowledge reports within 48 hours and provide an initial assessment within 7 days. We will coordinate a disclosure timeline with you.

## Scope

- Application code in this repository
- Dependencies declared in `pyproject.toml`

Out of scope: third-party services (Redis, Neo4j, Ollama, OpenAI) and their upstream vulnerabilities.

## Disclosure

Once a fix is available, we will document the change in `CHANGELOG.md` and credit reporters (if desired).
