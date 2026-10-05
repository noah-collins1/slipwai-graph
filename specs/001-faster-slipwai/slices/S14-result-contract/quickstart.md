# Quickstart: S14-result-contract — the demo script

The demo runs on a project generated from this branch (D136 item 3), never on this repository, whose own
`delivery/` gets the new briefs only through a person's `slipwai migrate`. Scratch under `/tmp/s14/` only.

## 1. Generate the project

```sh
rm -rf /tmp/s14/demo && mkdir -p /tmp/s14
/home/noahc/math/slipwai-graph-S14-result-contract/slipwai generate demo --output /tmp/s14 \
  --no-init --no-install --skip-checks
cd /tmp/s14/demo && git init -q && git add -A && git commit -qm generated
```

Expect `agents/drive-*.md` (ten) each ending its shared part with the result-contract paragraph and its own status
set, `docs/result-contract.md`, `scripts/hand_backs.py`, and a `commands/drive.md` with *What every delegate hands
back*.

## 2. Real hand-backs through the project's own headless harness

Project the agents (`make agents`), open a slice folder (`specs/f/slices/S1/` with a two-line `spec.md`), and
dispatch at least one real delegate per kind the ladder sends — `drive-gaps` over the spec, `drive-tasks` over a
one-rule plan — through the project's headless harness (`claude -p` on this machine; `CRUISE_HARNESS_COMMAND` may
wrap it, never replace it with a script that prints hand-backs). Feed each hand-back to

```sh
python3 scripts/check-decisions.py --hand-back specs/f/slices/S1 drive-gaps gaps < handback.txt
```

and, for one without a block, continue the same delegate once asking only for it; record `--hand-back-missing` where
it still has none. Record here: the project's axes, the harness and its version, and **the share of real hand-backs
that carried a passing block** (n of m).

| Axes | Harness | Hand-backs with a block |
|---|---|---|
| *(filled at the demo)* | | |

## 3. The two seeded fixtures (the checker paths)

- **No block** — a `benchmark.json` with one delegated `gaps` entry and a record with nothing for it:
  `python3 scripts/check-decisions.py --hand-backs specs/f/slices/S2` prints
  `gaps … drive-gaps: nothing recorded — a finding for converge` and `with a result contract: 0 of 1`.
- **Malformed** — a record whose block has `"status": "green"` for `drive-hand`: `make check-decisions` exits 1 with
  one line naming `hand-backs.md`, the entry's heading and `status`.

## 4. Nothing older is refused

`make check-decisions` on the project as generated (no record anywhere) prints the same line it did before this
release; `make benchmark` prints no hand-back line for a slice with no delegated stage.
