# Quickstart: S39-benchmark-elapsed — the demo script

The demo (AC-S39-11) runs the **asset copy** of the script, from a scratch clone of this slice's worktree (the
script's project root is the nearest directory above it holding `project.json`, so the clone is its own root, and the
cruise log can sit beside it without touching the worktree), over the real records of iterations 23–24 and the real
transcripts of this machine. It never runs this repository's `delivery/scripts/` (a control; it gets S39 only through
a person's `slipwai migrate`), never writes under `/home/noahc/math/slipwai-graph` or the worktree, and reads
`~/.claude/projects/-home-noahc-math-slipwai-graph/` without writing. Scratch under `/tmp/s39/` only. The timings are
reported, not judged against a threshold. The clone holds what is committed: commit first.

```sh
W=/home/noahc/math/slipwai-graph-S39-benchmark-elapsed
mkdir -p /tmp/s39
rm -rf /tmp/s39/demo && git clone -q $W /tmp/s39/demo
cp /home/noahc/math/slipwai-graph/specs/cruise-log.jsonl /tmp/s39/demo/specs/cruise-log.jsonl   # the log is untracked
cd /tmp/s39/demo
S=assets/toolkit/scripts/agents/benchmark.py
```

## 1. The aggregate

```sh
time python3 -B $S > /tmp/s39/aggregate.txt
```

Expect: the slice table's third column headed `stage time`, a `re-entered` column where `rework` was; the feature
line naming `stage time … in all`, `elapsed …` and `time with any slice in flight …` as three figures; a waiting
table with `elapsed`, `worked`, `dependency`, `worker`, `review`, `integration`, `unattributed`, `rework`, `cost`;
three decision-health lines reading `unknown — no decision entry carries a Reversibility: line` with no `%`.

## 2. S08 against figures derived by hand

```sh
python3 -B $S --json > /tmp/s39/all.json
python3 -B -c "import json; r=[x for x in json.load(open('/tmp/s39/all.json')) if x['slice']=='S08-scoped-mutation'][0]; print(json.dumps({k:r[k] for k in ('elapsed','stage_seconds','worked_seconds','waiting','rework','moments','read_from')}, indent=1))"
```

Derive the same by hand the way the code derives it — the oldest commit touching the file *whose copy holds the id*
(a row beginning `| <id> |`, backticked or bare), not a pickaxe, which lists a commit only when a count changes —
and the merge as the first-parent merge commit whose subject names the slice and does not say `into slice/<id>`:

```sh
F=specs/001-faster-slipwai
first() { for c in $(git log --reverse --format=%H -- "$1"); do
  git show "$c:$1" 2>/dev/null | grep -Eq "$2" && { git log -1 --format='%h %ct %cI' "$c"; return; }; done; }
row() { echo "^[[:space:]]*\\|[[:space:]]*\`?$1\`?[[:space:]]*\\|"; }
first $F/story-split.md "S08-scoped-mutation"                                    # added: d3a0926
first $F/slices/README.md "$(row S04-parallel-gate)"                             # S04 done: b31c864 → ready
first $F/slices/README.md "$(row S08-scoped-mutation)"                           # accepted: c88fe2f
git log --merges --first-parent --fixed-strings --grep=slice/S08-scoped-mutation --format='%h %ct %cI'  # merged: 3138416
first $F/slices/README.md "$(row S06-scoped-gate)"                               # S06 lands: 1d6cc17
```

- **elapsed** = accepted − ready (expected 133 433 s: 2026-10-04T18:13:05Z → 2026-10-06T07:16:58Z).
- **stage time** = Σ `seconds` over S08's 17 entries in `$F/slices/S08-scoped-mutation/benchmark.json` (none is cut
  off).
- **worked** = the union of those brackets inside [ready, accepted] (they do not overlap one another, so it equals
  the stage time, less nothing).
- **integration** = 03:14:44Z → 07:16:58Z (14 534 s) less the `adversary` (1 002 s) and last `implement` (2 537 s)
  brackets.
- **dependency** = S08's accepted demo end 00:31:54Z → S06's row 03:13:46Z (9 712 s), less any S08 bracket in it.
- **review** = the parks in [ready, accepted]: for each cruise-log row ending `cruise: stopped: human`, its `ended` →
  the next row's `started`, clipped to the interval, less S08 brackets.
- **worker** = from the cruise log's first row's `started` (before ready here, so from ready) to accepted — time
  between and after the logged iterations included, *outside any iteration* (AC-S39-2) — less worked, the causes
  above, and parks.
- **unattributed** = elapsed − the rest. Check: every part sums to elapsed exactly.

## 3. The S08 implement of 17:17–18:53Z

```sh
python3 -B -c "import json; r=[x for x in json.load(open('/tmp/s39/all.json')) if x['slice']=='S08-scoped-mutation'][0]; e=[e for e in r['entries'] if e['started']=='2026-10-05T17:17:50Z'][0]; print(e)"
```

Expect its `delegates` to name only S08's (`S08 US2 implement T002-T009` and helpers under S08's `drive-slice`), none
beginning `S06` or `S14`; and its tokens lower than the recorded `usage` (the page's `in`/`out` for that row, which
are as recorded and unchanged).

## 4. Tokens are conserved

```sh
python3 -B - <<'EOF'
import json, glob, os
seen, total = set(), 0
base = os.path.expanduser('~/.claude/projects/-home-noahc-math-slipwai-graph/d883234c-5eb4-40de-976d-81f2874b2842')
for path in [base + '.jsonl', *sorted(glob.glob(base + '/subagents/*.jsonl'))]:
    for line in open(path, encoding='utf-8', errors='replace'):
        if '"usage"' not in line: continue
        try: item = json.loads(line)
        except ValueError: continue
        m = item.get('message') or {}; u = m.get('usage'); k = item.get('requestId') or m.get('id') or item.get('uuid')
        if item.get('type') != 'assistant' or not isinstance(u, dict) or not k or k in seen: continue
        seen.add(k); total += sum(u.get(f) or 0 for f in ('input_tokens','output_tokens','cache_read_input_tokens','cache_creation_input_tokens') if isinstance(u.get(f), int))
print(total)
EOF
```

Expect that number to equal the `d883234c…` session's `total` in the feature record's `session_totals` (which the
script reads from the transcript, not as `attributed + shared`), and the records to account for all of it: the sum,
over every record, of its `cost.sessions` for that session, plus that session's `shared`, is the same number.

```sh
python3 -B -c "
import json
rows = json.load(open('/tmp/s39/all.json')); name = 'd883234c-5eb4-40de-976d-81f2874b2842'
mine = sum(r['cost']['sessions'].get(name, 0) for r in rows)
whole = next(r['session_totals'][name] for r in rows if 'session_totals' in r)
print(mine, whole['shared'], mine + whole['shared'], whole['total'])"
```

## 5. The page

```sh
python3 -B $S overview 001-faster-slipwai
git diff --stat specs/001-faster-slipwai/benchmark.md      # in the scratch clone: it is thrown away in step 6
```

Expect the page's *Reading these numbers* to carry the sentence on elapsed against stage time; the stage tables'
column `stage time`; each slice heading with stage time and elapsed under their names. The page is written in the
scratch clone only; the worktree's own is untouched.

## 6. Clean up

```sh
cd $W
rm -rf /tmp/s39/demo /tmp/s39/aggregate.txt /tmp/s39/all.json
git -C $W status --short     # nothing the demo made
```
