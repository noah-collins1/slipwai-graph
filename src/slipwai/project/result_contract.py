"""The words that say how every delegate ends its hand-back, and who records it (ADR 0006, D134, D136).

Their own module because `agents.py`, `commands.py` and `cruise.py` sit at the 350-line budget. The shape itself is
`docs/result-contract.md`, and `assets/toolkit/scripts/hand_backs.py` is the same shape as code; `STATUSES` here is a
copy of that script's table, held equal to it by `tests/test_result_contract_briefs.py`, because the factory cannot
import a script a project runs.
"""
from __future__ import annotations

import textwrap

from ..layout import Layout
from .cruise_agents import DECISIONS

PAGE = "docs/result-contract.md"
# Per delegate type, the words `status` may take (D134 section 3).
STATUSES: dict[str, tuple[str, ...]] = {
    "drive-gaps": ("gaps", "none"),
    "drive-skipper": ("decided", "unavailable"),
    "drive-adversary": ("broken", "held"),
    "drive-bosun": ("unblocked", "cannot", "catastrophic"),
    "drive-converge": ("converged", "not-converged", "incomplete"),
    "drive-hand": ("accepted", "behaviour", "implementation"),
    "drive-implement": ("green", "partial", "stopped"),
    "drive-mutation": ("scored", "failed-run"),
    "drive-slice": ("converged", "stopped"),
    "drive-tasks": ("written", "contradiction"),
}


# Which stages owe the record a block, and which word names a stage in it (T012: the count and the ladder agree).
OWES = ("A stage owes a block only when a typed `drive-*` delegate that belongs to the stage ran: the untyped "
        "helpers it started (Explore, general-purpose) and a `drive-slice`'s own context owe none, and a delegate the "
        "harness could not attribute is said so and never a finding.")
STAGE = ("`<stage>` is the name of the stage's open benchmark entry — the word `benchmark.py start` was given — so "
         "the record and `benchmark.json` name a stage the same way.")


def spelled(words: tuple[str, ...]) -> str:
    """`a` or `b`; `a`, `b` or `c`."""
    quoted = [f"`{word}`" for word in words]
    return f"{', '.join(quoted[:-1])} or {quoted[-1]}"


def brief_paragraph(name: str) -> str:
    """The paragraph every type's standing brief carries, after its own part."""
    return f"""## What you hand back

End your hand-back with one fenced block whose info string is exactly `result-contract`, holding one JSON object:
the thirteen fields [{PAGE}]({PAGE}) lists, in that order. In yours `delegate` is `{name}` and `status` is
{spelled(STATUSES[name])}. Whatever you started and did not finish, decided, assumed or left open goes inside that
one block — `unresolved`, `decisions`, `assumptions` — and nowhere after it: the block is the last thing you write.
Helpers you start (Explore, general-purpose, a fan-out group) get no block and no entry of their own; what they did
is reported in your own block.
The session that delegated you appends it, verbatim, to the record; it never writes a block for you."""


def hand_backs_section(layout: Layout) -> str:
    """`commands/drive.md`'s *What every delegate hands back*: who appends the block, when, and what a miss costs."""
    return f"""## What every delegate hands back

Every delegate ends its hand-back with one `result-contract` block ([{PAGE}]({PAGE}) has the shape). **This session
appends it**, verbatim, before it closes the stage's benchmark entry:

```sh
python3 scripts/check-decisions.py --hand-back <dir> <type> <stage>   # the whole hand-back on stdin
```

`<dir>` is the slice's own folder, `specs/<feature>/slices/<id>`, for the slice's stages, and `specs/<feature>` for
the feature-level ones: the split, the ready set's `drive-slice` delegates (stage `ready-set`) and the completion
audit. {STAGE} The verb checks the block with the gate's own function, writes the heading itself, and appends nothing when a
field fails — it prints the field. `{layout.make} check-decisions` holds every record to the same shape.

A hand-back with no block, or one the verb refused, gets **one continuation** of the same delegate asking only for the
block. A continuation recorded after the stage's benchmark entry has closed passes `--started <instant>` to either
verb, the instant the `--hand-backs` line names (the converge, demo-stop or adversary-stop line); on time, the verb
finds the open entry itself. If that does not produce one, record the miss with a reason:

```sh
python3 scripts/check-decisions.py --hand-back-missing <dir> <type> <stage> <reason>
```

The reason is `refused: <the delegate's words>`, `malformed: <field>` or `no continuation`; a delegate that was
stopped is recorded `stopped: <reason>`. The stage is never re-run for a block, and this session never writes a block
for a delegate — one it wrote would be the session grading the work it was handed.
A stage run in this context has no delegate, so it has no entry and nothing to record.

{OWES}

Two stops check the record, and a miss at either is a task, closed with one continuation, and never re-opens converge.
Before the hand, at the demo stop, read the hand-backs since the last converge pass; at the adversary stop, those of
the hand, the adversary and mutation:

```sh
python3 scripts/check-decisions.py --hand-backs specs/<feature>/slices/<id>
```
"""


def converge_sentence(layout: Layout, indent: str = "") -> str:
    """The converge rung's and the converge brief's reading of the record; `indent` is the rung's list continuation."""
    lines = (
        "Converge also reads the record: `python3 scripts/check-decisions.py --hand-backs specs/<feature>/slices/<id>`",
        "lists, for each delegated stage in `benchmark.json`, whether `hand-backs.md` holds its `result-contract` block,",
        "a `Missing:` line or nothing. A delegated stage without a passing `result-contract` block is a finding,",
        "naming the stage and the delegate type, graded `MEDIUM`: one continuation of that delegate closes it before",
        "Phase 4.",
        *textwrap.wrap(OWES, 112),
        f"`{layout.make} check-decisions` holds what is recorded to the shape.",
    )
    return f"\n{indent}".join(lines)


def cruise_sentences(layout: Layout) -> str:
    """`commands/cruise.md`: where the skipper's entry and every skipper, hand and bosun block go."""
    return f"""**Every skipper, hand and bosun dispatch is recorded the same way** ([{PAGE}]({PAGE})): the skipper's entry
goes to `{DECISIONS}` as above, and its `result-contract` block to the record with
`python3 scripts/check-decisions.py --hand-back <dir> drive-skipper <stage>`; the hand's and the bosun's blocks the
same, each before the stage's benchmark entry closes. The skipper's own `D<n>` goes in the block's `change_summary` and
never in `decisions`, which lists only the standing entries the work relied on, whether its `status` is `decided` or
`unavailable`. An `unavailable` answer is an entry too, appended at `Status: standing` under the number it was given,
so that number resolves; the report lists it among the entries a person has not reviewed, and a person overrides it as
they override any entry. *What every delegate hands back* in `commands/drive.md` has
the continuation and the `Missing:` forms, and the `<stage>` is the name of the stage's open benchmark entry
(`skipper`, `hand`, `bosun`); `{layout.make} check-decisions` holds the record to the shape."""


def adversary_sentence() -> str:
    """`commands/adversary.md`: each adversary's block is appended before the `adversary` entry ends (B3, T032)."""
    return f"""Each adversary ends its hand-back with a `result-contract` block ([{PAGE}]({PAGE})). **Append each one, verbatim,
before you end the `adversary` benchmark entry**, with
`python3 scripts/check-decisions.py --hand-back specs/<feature>/slices/<id> drive-adversary adversary`; a hand-back with
no block, or one the verb refused, gets one continuation, and where that fails, `--hand-back-missing` records the miss.
*What every delegate hands back* in `commands/drive.md` has both forms."""


def audit_sentence() -> str:
    """The completion audit: its delegates' blocks are appended, and its `drive-gaps` delegates are the backstop (T025)."""
    return f"""Each audit `drive-gaps` delegate ends with a `result-contract` block ([{PAGE}]({PAGE})): append it, a
feature-level stage, with `python3 scripts/check-decisions.py --hand-back specs/<feature> drive-gaps audit` before the
audit is written up. The audit is also the backstop for the two stops above: each audit `drive-gaps` delegate also runs
`python3 scripts/check-decisions.py --hand-backs` over every slice, and a delegated stage with neither a passing block
nor a `Missing:` line is an audit finding."""


def slice_record_sentence() -> str:
    """What `drive-slice` adds: inside its worktree it is the dispatching session, and its own block goes up."""
    return f"""**Your sub-delegates' hand-backs.** Inside your worktree you are the session that delegated them: append each
block to this slice's record, `specs/<feature>/slices/<id>/hand-backs.md`, with
`python3 scripts/check-decisions.py --hand-back specs/<feature>/slices/<id> <type> <stage>` before you close the
stage's benchmark entry. Your own block goes to the session above you, which appends it to
`specs/<feature>/hand-backs.md`, stage `ready-set` — never to this slice's record, which two branches would both
write. {STAGE}"""
