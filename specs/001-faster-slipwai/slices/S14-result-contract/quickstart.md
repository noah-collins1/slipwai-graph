# Quickstart: S14-result-contract — the demo script

The demo runs on a project generated from this branch (D136 item 3), never on this repository, whose own
`delivery/` gets the new briefs only through a person's `slipwai migrate`. Scratch under `/tmp/s14/` only. Every
command below was run once in `/tmp/s14/demo` (Claude Code 2.1.289 on this machine) up to the point where a real
model call is needed; the expected lines are what the code printed.

## 1. Generate the project and give it an integration

```sh
rm -rf /tmp/s14/demo && mkdir -p /tmp/s14 && cd /tmp/s14
/home/noahc/math/slipwai-graph-S14-result-contract/slipwai generate demo --output /tmp/s14 \
  --no-init --no-install --skip-checks
cd /tmp/s14/demo
./init --integration claude        # Spec Kit via uvx, then the agent projection; needs the network once
git add -A && git -c user.email=a@b -c user.name=x commit -qm init
```

`generate` makes the repository and its first commit (`Scaffold demo`) itself. `--no-init` leaves no integration, and
`make agents` refuses until one exists (`cannot determine the selected integration; rerun ./init --integration
<agent>`); `./init --integration claude` is the step that gives it one. It ends with
`Project skills, commands and agent types installed for Claude Code (claude).` and a reminder that the harness reads
its agent types once, at session start.

Expect `agents/drive-*.md` (ten, and the same ten projected under `.claude/agents/`) each carrying
`## What you hand back` with the result-contract paragraph, its own status set and the sentence that helpers it starts
get no block of their own; `docs/result-contract.md`; `scripts/hand_backs.py`; and `commands/drive.md` with
*What every delegate hands back* once.

```sh
ls agents | wc -l                                              # 10
ls docs/result-contract.md scripts/hand_backs.py               # both listed
grep -c "What every delegate hands back" commands/drive.md     # 1
grep -l "What you hand back" agents/*.md | wc -l               # 10
```

## 2. Real hand-backs through the project's own headless harness

Open a slice folder with a two-line spec, then dispatch each typed delegate as the session's own agent, so that the
final message captured is the delegate's, not an outer session's:

```sh
mkdir -p specs/f/slices/S1
printf '# S1\n\nA visitor can add an item to a list.\nAn empty name is refused.\n' > specs/f/slices/S1/spec.md
claude -p "Read specs/f/slices/S1/spec.md and report the gaps in it." --agent drive-gaps \
  --output-format text --permission-mode acceptEdits > /tmp/s14/handback.txt
```

This is the registry's `claude` headless command (`claude -p {prompt} --output-format stream-json --verbose
{permissions}`) with `--agent <type>` added and `--output-format text` so the file holds the final text and nothing
else; `CRUISE_HARNESS_COMMAND` may wrap it, never replace it with a script that prints hand-backs. For `drive-tasks`
the same command is run with `--agent drive-tasks` over a one-rule `plan.md`. Do each once; a call that needs the model
is the point at which this script stops being checkable without one.

Feed each hand-back to the verb. With a hand-back holding one passing block (a hand-written stand-in is used below to
show the output; the demo uses the file the model wrote):

```sh
python3 scripts/check-decisions.py --hand-back specs/f/slices/S1 drive-gaps gaps < /tmp/s14/handback.txt
```

- exit 0, nothing printed, and `specs/f/slices/S1/hand-backs.md` starts `# Hand-backs — S1`, then
  `## <UTC time> — drive-gaps — gaps`, then the fence verbatim.
- `python3 scripts/check-decisions.py` then prints
  `check-decisions: 0 decision(s) in 0 file(s), 0 demo(s) in 0 log(s), 1 hand-back(s) in 1 record(s), every field present and every path in the tree, every done slice in the adversary log`
  and exits 0.
- Running the same verb again with the same file appends nothing, exits 0 and prints
  `check-decisions: note: specs/f/slices/S1/hand-backs.md already ends this drive-gaps gaps entry with the same content; nothing appended`.
- A hand-back with no block (`: > /tmp/s14/empty.txt`, then the same verb with `< /tmp/s14/empty.txt`) prints
  `check-decisions: no result-contract block in the hand-back` and exits 1; continue the same delegate once asking only
  for the block, and where it still has none:

```sh
python3 scripts/check-decisions.py --hand-back-missing specs/f/slices/S1 drive-tasks tasks no continuation
```

  exit 0, nothing printed, and the record gains `## <UTC time> — drive-tasks — tasks` and `- **Missing:** no continuation`.

Record here: the project's axes, the harness and its version, and **the share of real hand-backs that carried a
passing block** (n of m).

| Axes | Harness | Hand-backs with a block |
|---|---|---|
| *(filled at the demo)* | | |

## 3. The two seeded fixtures (the checker paths)

- **No block** — a slice whose `benchmark.json` has one ended, delegated `gaps` entry naming `drive-gaps` in its
  `agents`, and no record:

  ```sh
  mkdir -p specs/f/slices/S2
  cat > specs/f/slices/S2/benchmark.json <<'E'
  {"feature": "f", "slice": "S2", "stages": [
   {"stage": "gaps", "started": "2026-10-05T18:30:00Z", "ended": "2026-10-05T18:40:00Z", "seconds": 600, "signals": {},
    "delegated": true, "agents": ["drive-gaps"], "usage": {"source": "claude", "reason": null}}]}
  E
  python3 scripts/check-decisions.py --hand-backs specs/f/slices/S2
  ```

  prints, and exits 0,

  ```text
  hand-backs: gaps 2026-10-05T18:30:00Z drive-gaps: nothing recorded — a finding for converge
  hand-backs: with a result contract: 0 of 1
  ```

  A trailing slash (`specs/f/slices/S2/`) prints the same. `python3 scripts/agents/benchmark.py` prints, for the
  slice, `S2: hand-backs with a result contract: 0 of 1`. An entry whose only `agents` are `["Explore"]`, or
  `["drive-slice"]`, owes nothing and prints neither a line nor a count.
- **Malformed** — a record whose block has `"status": "green"` for `drive-hand`
  (`specs/f/slices/S3/hand-backs.md`, heading `## 2026-10-05T19:00:00Z — drive-hand — demo`):
  `make check-decisions` runs `python3 scripts/check-decisions.py`, which prints on stderr

  ```text
  check-decisions: the record is not in the shape commands/cruise.md shows

    specs/f/slices/S3/hand-backs.md:3: ## 2026-10-05T19:00:00Z — drive-hand — demo — status: 'green' is not one of accepted, behaviour, implementation

  ```

  and exits 1 (make reports `Error 1` and itself exits 2).

## 4. Nothing older is refused

Run this on the project as generated, before steps 2 and 3 add a record (a fresh `/tmp/s14/demo`):
`make check-decisions` prints `check-decisions: no decisions.md or demo-log.md under specs/ — nothing recorded yet` and
exits 0, the line it printed before this release; `make benchmark` prints
`benchmark: no record yet — /drive writes specs/<feature>/slices/<id>/benchmark.json from its next stage`, with no
hand-back line.
