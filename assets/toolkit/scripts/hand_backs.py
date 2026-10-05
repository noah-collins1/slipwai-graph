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


def whole(value: object) -> bool:
    """An integer, which JSON's `true` (a `bool`, an `int` subclass) is not."""
    return isinstance(value, int) and not isinstance(value, bool)


def text_fault(value: object) -> str | None:
    if not isinstance(value, str):
        return f"{value!r} is not a string"
    return None if value.strip() else "is empty; it says something"


def list_fault(value: object) -> str | None:
    if not isinstance(value, list):
        return f"{value!r} is not a list of strings"
    odd = [item for item in value if not isinstance(item, str)]
    return f"{odd[0]!r} is not a string; every item of the list is one" if odd else None


def path_fault(path: str) -> str | None:
    """A path is repository-relative: no leading `/` or `\\`, no `X:` drive, no `..` segment."""
    if path.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", path):
        return f"{path!r} is absolute; a path is repository-relative"
    if ".." in re.split(r"[/\\]", path):
        return f"{path!r} has a `..` segment; a path stays inside the repository"
    return None


def difficulty_fault(value: object) -> str | None:
    shape = "is an object of exactly an integer `score` 1-5 and a non-empty string `reason`"
    if not isinstance(value, dict) or set(value) != {"score", "reason"}:
        return f"{value!r} is not an object of exactly `score` and `reason`; it {shape}"
    score, reason = value["score"], value["reason"]
    if not whole(score) or not 1 <= score <= 5 or not isinstance(reason, str) or not reason.strip():
        return f"{value!r} is not valid; it {shape}"
    return None


def decision_fault(item: object, known: set[str] | None) -> str | None:
    if not isinstance(item, str) or not re.fullmatch(r"D[0-9]+", item):
        return f"{item!r} is not a decision id `D<n>`"
    if known is not None and item not in known:
        return f"{item!r} names no `## {item} — ` entry in the feature's decisions.md"
    return None


def items_faults(name: str, items: list[str], known: set[str] | None) -> list[str]:
    """The faults of each item of a list field whose items mean something beyond being strings."""
    if name == "files_changed":
        return [fault for fault in map(path_fault, items) if fault]
    if name == "decisions":
        return [fault for fault in (decision_fault(item, known) for item in items) if fault]
    return []


def field_faults(name: str, kind: str, value: object, block: dict[str, Any], heading_type: str,
                 known: set[str] | None) -> list[str]:
    """The faults of one present field."""
    if name == "contract":
        return [] if whole(value) and value == SCHEMA else [f"{value!r} is not the integer {SCHEMA}"]
    if name == "delegate":
        if not isinstance(value, str) or value not in STATUSES:
            return [f"{value!r} is not one of {', '.join(STATUSES)}"]
        return [] if value == heading_type else [f"{value!r} differs from the heading's {heading_type!r}"]
    if name == "status":
        delegate = block.get("delegate")
        allowed = STATUSES.get(delegate, ()) if isinstance(delegate, str) else ()
        return [] if not allowed or value in allowed else [f"{value!r} is not one of {', '.join(allowed)}"]
    fault = difficulty_fault(value) if kind == "object" else text_fault(value) if kind == "string" else list_fault(value)
    if fault:
        return [fault]
    return items_faults(name, value, known) if kind == "list" else []  # type: ignore[arg-type]


def check_block(block: object, heading_type: str, known: set[str] | None) -> list[str]:
    """The faults of one parsed block, each `<field>: <fault>`; `known` is the feature's `D<n>` ids."""
    if not isinstance(block, dict):
        return [f"block: {block!r} is not a JSON object"]
    faults: list[str] = []
    for name, kind in FIELDS:
        if name not in block:
            faults.append(f"{name}: absent; the block holds all {len(FIELDS)} fields")
            continue
        faults += [f"{name}: {fault}" for fault in field_faults(name, kind, block[name], block, heading_type, known)]
    return faults


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
