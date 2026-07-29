# Versioning Scheme

UPCP follows [Semantic Versioning 2.0](https://semver.org/) with a pre-1.0 development convention.

## Current Version

Check `pyproject.toml` and `frontend/package.json` for the authoritative current version.

## Scheme

```
0.MINOR.PATCH
│    │      │
│    │      └─ fix, polish, refactor (sprint within milestone)
│    │
│    └─ milestone completed (new features)
│
└─ always 0 until 1.0.0
```

### Minor version increments when:

- A milestone (M0, M1, ...) is completed
- A significant batch of audit fixes is done
- A new major feature set lands

### Patch version increments when:

- Bug fixes within a milestone
- Refactoring (no new features)
- Documentation updates
- Test coverage improvements
- UX polish

### 1.0.0 criteria

All of the following must be true:

1. All Critical/High audit items closed
2. Dashboard shows real data (not hardcoded)
3. Auth flow works end-to-end
4. Test coverage on auth + core pages
5. Bundle < 300KB
6. No broken buttons/forms

## Version History

| Version | Milestone | Date |
|---------|-----------|------|
| 0.1.0 | Initial scaffold | 2026-07-24 |
| 0.2.0 | M0 — Foundation | 2026-07-24 |
| 0.3.0 | M1 — Projects & RBAC | 2026-07-24 |
| 0.4.0 | M2 — Structure, Delivery, Quality | 2026-07-25 |
| 0.5.0 | M3 — Git Read | 2026-07-25 |
| 0.6.0 | M4 — MCP & CLI | 2026-07-26 |
| 0.7.0 | M5 — Frontend Foundation | 2026-07-26 |
| 0.8.0 | M6 — Reports & LLM | 2026-07-26 |
| 0.9.0 | M7 — Auth, RBAC, Agents | 2026-07-27 |
| 0.10.0 | M8 — Runtime Foundation | 2026-07-27 |
| 0.11.0 | M9 — Agent Workflow MVP | 2026-07-27 |
| 0.12.0 | M10 — Evidence & Review | 2026-07-27 |
| 0.13.0 | M11 — Human Control UX | 2026-07-27 |

## How to Update Versions

### Before starting work on a new milestone:

1. Decide if this milestone warrants a minor bump (new features) or patch (fixes only)
2. Update `pyproject.toml` — `version = "0.X.Y"`
3. Update `frontend/package.json` — `"version": "0.X.Y"`
4. Update this file's version history table
5. Update `CHANGELOG.md` — move `[Unreleased]` items to the new version section

### Commit convention:

```
chore: bump version to 0.X.Y — <milestone summary>
```

### Files to update:

| File | Field |
|------|-------|
| `pyproject.toml` | `version = "0.X.Y"` |
| `frontend/package.json` | `"version": "0.X.Y"` |
| `CHANGELOG.md` | New section `## [0.X.Y] - YYYY-MM-DD` |
| `VERSIONING.md` | Version history table |

## Rules

- **Never skip versions** in the history (no jumping from 0.3.0 to 0.5.0)
- **Never retroactively change** released versions
- **Git tags** are created at 1.0.0+ only (no tags for 0.x.y)
- **Both** pyproject.toml and package.json must match
- **CHANGELOG.md** is the human-readable history; version files are the source of truth for tooling
