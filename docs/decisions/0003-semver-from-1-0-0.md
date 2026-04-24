# ADR-0003: Adopt SemVer starting at 1.0.0

- **Status**: accepted
- **Date**: 2026-04-24

## Context

`granola_sync` is a Python package with a public library API (`sync_all`, `sync_folder`, `create_mapping`, …) **plus** an optional GUI. It's shipped — V1 is in production on the developer's own machine and the README advertises it as importable by other apps. Three versioning schemes were candidates:

1. **ZeroVer** (`0.x.y` forever) — common in early-stage packages, but [explicitly recognized as an anti-pattern](https://0ver.org/) once a project has real users. Makes the version number meaningless.
2. **CalVer** (`2026.04`) — great for continuously-deployed user apps with no API (Ubuntu, JetBrains). `granola_sync` has a public library API, so the breaking-change signal is load-bearing.
3. **SemVer** (`MAJOR.MINOR.PATCH`) — designed for libraries with public APIs. Matches the project's existing V1 / V1.1 / V2 mental model.

## Decision

`granola_sync` adopts **[Semantic Versioning 2.0.0](https://semver.org/)** starting at **`1.0.0`** (the current shipped state on `main` as of this ADR).

- `MAJOR` bump = breaking public API change.
- `MINOR` bump = backward-compatible new feature.
- `PATCH` bump = backward-compatible bug fix.

Internal prose / docs use the short form ("V1", "V2.1"). Git tags and PyPI releases use the full triple (`v1.1.0`, `v2.0.0`).

Pre-existing merged work is retroactively grouped: everything merged up to 2026-04-23 is `v1.0.0`; the LLM transcript formatting + filename fix is `v1.1.0` (2026-04-24).

## Alternatives considered

- **ZeroVer** (`0.x.y`) — rejected: V1 is shipped and the version number should carry real meaning for downstream pinners.
- **CalVer** (`2026.04`) — rejected: the library consumers (including future AI tools that import `granola_sync`) need the breaking-change signal SemVer provides.

## Consequences

- **Good**: PyPI, GitHub Releases, `pip install granola-sync==2.0.0`, `uv`, `poetry` all understand SemVer out of the box. Downstream consumers can pin with confidence. Each bump carries clear meaning.
- **Trade-off**: marketing-style version bumps (a huge V2 UI that doesn't break the library API) have to be communicated via changelog / release notes rather than the version number alone.
- **Follow-ups**: first git tag (`v1.0.0`) against the state of `main` when PR #3 was merged; second tag (`v1.1.0`) against the state after PR #4.
