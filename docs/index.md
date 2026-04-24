# Documentation index

One-screen map of the docs tree. Start here.

| Path | Purpose |
|---|---|
| [`/CHANGELOG.md`](../CHANGELOG.md) | User-facing release notes. Keep a Changelog format, SemVer. |
| [`ROADMAP.md`](ROADMAP.md) | Uncommitted future ideas — a pick-from pool for the next version. |
| [`tech-debt.md`](tech-debt.md) | Systemic / cross-cutting debt. Code-local debt lives in GitHub Issues with the `tech-debt` label. |
| [`decisions/`](decisions/) | Architecture Decision Records (ADRs). Start with [`decisions/README.md`](decisions/README.md). |
| [`versions/`](versions/) | Per-major-version specs. Start with [`versions/README.md`](versions/README.md) for the status matrix. |

## Quick orientation

- **Current version**: see [`versions/README.md`](versions/README.md) — look for the row marked `IN PROGRESS`.
- **Why we did X**: search [`decisions/`](decisions/) — each ADR has Context, Decision, Alternatives, Consequences.
- **What's next**: [`ROADMAP.md`](ROADMAP.md). Nothing in there is committed; anything can be promoted into the next `versions/vN.md` when work begins.
- **Known pain**: [`tech-debt.md`](tech-debt.md) + GitHub Issues filtered by `tech-debt` label.

## For AI collaborators

- Version docs (`versions/vN.md`) open with a YAML-ish header whose `status:` field is one of `PLANNED`, `IN PROGRESS`, or `FROZEN`. A FROZEN spec is a historical record and must not be edited; corrections go in a new ADR or the next version's spec.
- ADR filenames are zero-padded monotonic (`0001-…`, `0002-…`). Never renumber. If a decision is overturned, write a new ADR whose status supersedes the old one's.
