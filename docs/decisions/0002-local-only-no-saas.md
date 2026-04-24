# ADR-0002: Keep the app local-only; no hosted SaaS version

- **Status**: accepted
- **Date**: 2026-04-24

## Context

A hosted SaaS version of `granola_sync` would let users configure mappings in a browser and run syncs from a server. On the surface that removes install friction.

But Granola API keys (`grn_...`) grant read access to every meeting transcript the user has ever recorded. For student users especially, that includes professor meetings, interviews, research conversations, and 1:1s — all of which would be on a third-party server under a SaaS model.

The actual deliverable is `.md` files **on the user's filesystem**. Any SaaS version would either require Chrome's File System Access API (Chrome-only, awkward UX) or force a per-sync download zip.

## Decision

`granola_sync` is and will remain **local**. API keys live in `config.json` on the user's disk. Sync runs in the user's Python process. No backend server. No telemetry.

## Alternatives considered

- **Full SaaS** — rejected for the trust/privacy reasons above. Plus hosting costs, compliance overhead, and the infra is all for something that's really just a personal cron job.
- **Hybrid (SaaS-configured mappings, local sync via downloaded config)** — rejected: added complexity with marginal gain. Users who need cross-machine config sync can put `config.json` in iCloud Drive / Dropbox themselves.

## Consequences

- **Good**: no infrastructure to run or pay for. No compliance / security overhead. API keys never leave the user's machine. Scheduled sync is free via OS-native schedulers (launchd / Task Scheduler).
- **Trade-off**: no frictionless "click this URL to start" onboarding — users must install the app (pip or downloaded binary).
- **Follow-ups**: revisit only if (a) user trust in a hosted model stops being the main blocker to adoption, or (b) Granola ships a fine-grained permission model so API keys can be scoped to single folders / read-only / time-limited.
