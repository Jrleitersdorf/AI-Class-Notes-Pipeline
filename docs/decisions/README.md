# Architecture Decision Records (ADRs)

Short documents that capture a significant technical decision, the context that forced it, and the alternatives considered. Future-you (or an AI collaborator) reads these to understand *why* the code looks the way it does, without having to reconstruct the reasoning from commit history.

## How to add one

1. Pick the next unused number. Look at the highest `NNNN-*.md` in this directory and add 1.
2. `cp 0000-template.md NNNN-kebab-case-title.md`.
3. Fill in every section. Keep it short — the value is in writing it down, not in length.
4. Add a row to the Index table below.
5. Commit.

**Never renumber.** If a decision is overturned, create a *new* ADR, set its status to `accepted`, and change the old ADR's status to `superseded by ADR-NNNN`. This preserves the historical reasoning.

## Index

| ID | Title | Status |
|---|---|---|
| [0001](0001-use-pywebview-for-v2-gui.md) | Use PyWebView + React for V2 GUI | accepted |
| [0002](0002-local-only-no-saas.md) | Keep the app local-only; no hosted SaaS version | accepted |
| [0003](0003-semver-from-1-0-0.md) | Adopt SemVer starting at 1.0.0 | accepted |
