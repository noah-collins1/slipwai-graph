# Data model: S03-verify-stamp

**The stamp** — one JSON object in `<git-dir>/slipwai/verify-stamp-<project>.json`, where `<git-dir>` is what
`git rev-parse --absolute-git-dir` answers for this checkout and `<project>` is a digest of the project's path
inside the repository (`git rev-parse --show-prefix`), so two projects in one repository have two files and the
file holds no path.

| Field | What it is |
|---|---|
| `key` | SHA-256 over the three parts below; what a later run compares, and what the reuse line abbreviates |
| `tree` | SHA-256 over: each covered file (path, kind, executable bit, raw bytes or link target or *missing*); the index's entries; `HEAD`'s name and commit; every ref under `refs/heads` and `refs/remotes`; the shallow boundary; each ignored input (bytes, or *absent*); each keyed variable (value, or *unset*) |
| `scripts` | SHA-256 over the `Makefile` and every covered file under `scripts/` |
| `tools` | an object: tool name → the first non-empty line it reported; and each Python service's interpreter as `pyvenv.cfg` records it |
| `passed` | the instant the last check passed, UTC, to the second |
| `result` | `pass` — a stamp is never written for anything else |

**The pending note** — `verify-stamp-<project>.pending`, beside it, written by `reuse` and removed by `record`:
the key computed before the first check, or the word that this run records nothing. A note left by a killed run is
overwritten by the next.
