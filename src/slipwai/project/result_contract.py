"""The words that say how every delegate ends its hand-back, and who records it (ADR 0006, D134, D136).

Their own module because `agents.py`, `commands.py` and `cruise.py` sit at the 350-line budget. The shape itself is
`docs/result-contract.md`, and `assets/toolkit/scripts/hand_backs.py` is the same shape as code; `STATUSES` here is a
copy of that script's table, held equal to it by `tests/test_result_contract_briefs.py`, because the factory cannot
import a script a project runs.
"""
from __future__ import annotations

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
The session that delegated you appends it, verbatim, to the record; it never writes a block for you."""


def slice_record_sentence() -> str:
    """What `drive-slice` adds: inside its worktree it is the dispatching session, and its own block goes up."""
    return """**Your sub-delegates' hand-backs.** Inside your worktree you are the session that delegated them: append each
block to this slice's record, `specs/<feature>/slices/<id>/hand-backs.md`, with
`python3 scripts/check-decisions.py --hand-back specs/<feature>/slices/<id> <type> <stage>` before you close the
stage's benchmark entry. Your own block goes to the session above you, which appends it to
`specs/<feature>/hand-backs.md`, stage `ready-set` — never to this slice's record, which two branches would both
write."""
