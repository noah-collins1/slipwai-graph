"""The result-contract block a delegate hands back, and the record it is appended to (ADR 0006, D134).

`docs/result-contract.md` is the shape in words; this is the same shape as code, so the gate and the dispatching
session hold a block to one function. Loaded by path, with bytecode off, by `check-decisions.py`; nothing here
prints or exits. A record is `hand-backs.md`: a preamble, then entries `## <UTC time> — drive-<name> — <stage>`,
each holding one fenced `result-contract` block.
"""
from __future__ import annotations

import json
import re
from typing import Any

SCHEMA = 1
FENCE = "result-contract"
HEADING = re.compile(r"^## (\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ) — (drive-[a-z]+) — ([a-z][a-z0-9-]*)$")

# The thirteen fields, in order, each with the kind of value it holds (the page's table is this one).
FIELDS: tuple[tuple[str, str], ...] = (
    ("contract", "integer"), ("delegate", "string"), ("scope", "string"), ("status", "string"),
    ("contracts_changed", "list"), ("invariants_checked", "list"), ("tests", "list"), ("decisions", "list"),
    ("assumptions", "list"), ("unresolved", "list"), ("change_summary", "string"), ("files_changed", "list"),
    ("difficulty_observed", "object"),
)
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


def newer(block: object) -> bool:
    """A block written under a later schema than this reads: passed with a note, no field held."""
    contract = block.get("contract") if isinstance(block, dict) else None
    return isinstance(contract, int) and not isinstance(contract, bool) and contract > SCHEMA


def check_block(block: object, heading_type: str, known: set[str] | None) -> list[str]:
    """The faults of one parsed block, each `<field>: <fault>`; `known` is the feature's `D<n>` ids."""
    return []


def extract(text: str) -> list[dict[str, Any]]:
    """The entries of a record: `line`, `heading`, `match` (the heading's parts or None) and `blocks`, the
    (line, body) of each `result-contract` fence in it."""
    entries: list[dict[str, Any]] = []
    lines = text.split("\n")
    for number, line in enumerate(lines, 1):
        if line.startswith("## "):
            entries.append({"line": number, "heading": line, "match": HEADING.match(line), "blocks": []})
        elif entries and line.strip() == f"```{FENCE}":
            end = next((i for i in range(number, len(lines)) if lines[i].strip() == "```"), None)
            if end is not None:
                entries[-1]["blocks"].append((number, "\n".join(lines[number:end])))
    return entries


def check_record(text: str, where: str, known: set[str] | None) -> tuple[list[str], list[str], int]:
    """Findings, notes and the count of blocks in one record's text; `where` is its path from the root."""
    findings: list[str] = []
    notes: list[str] = []
    count = 0
    for entry in extract(text):
        for _, body in entry["blocks"]:
            count += 1
            block = json.loads(body)
            at = f"{where}:{entry['line']}: {entry['heading']}"
            if newer(block):
                notes.append(f"check-decisions: note: {at} — contract {block['contract']} is newer than this "
                             "checker reads; its fields are not held")
                continue
            findings += [f"{at} — {fault}" for fault in check_block(block, entry["match"].group(2), known)]
    return findings, notes, count
