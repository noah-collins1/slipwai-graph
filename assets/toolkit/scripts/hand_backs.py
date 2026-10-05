"""The result-contract block a delegate hands back, and the record it is appended to (ADR 0006, D134).

`docs/result-contract.md` is the shape in words; this is the same shape as code, so the gate and the dispatching
session hold a block to one function. Loaded by path, with bytecode off, by `check-decisions.py`; nothing here
prints or exits. A record is `hand-backs.md`: a preamble, then entries `## <UTC time> — drive-<name> — <stage>`,
each holding one fenced `result-contract` block.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
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
    if os.pardir in re.split(r"[/\\]", path):
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


MISSING = re.compile(r"^- \*\*Missing:\*\* (\S.*)$")
SHAPE = "a heading `## <UTC time> — <drive-type> — <stage>`"


def extract(text: str) -> list[dict[str, Any]]:
    """The entries of a record, each `line`, `heading`, `match` (the heading's parts or None), `blocks` (the
    (line, body) of each `result-contract` fence), `missing` (the reasons of `- **Missing:**` lines) and `open`
    (the line of a `result-contract` fence no closing fence ended before the next heading). A fence with another
    info string is skipped whole, headings inside it included; text before the first heading is the file's own."""
    entries: list[dict[str, Any]] = []
    lines = text.split("\n")
    fence: tuple[str, int, list[str]] | None = None  # info string, line, body so far
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if fence is not None and stripped == "```":
            if fence[0] == FENCE and entries:
                entries[-1]["blocks"].append((fence[1], "\n".join(fence[2])))
            fence = None
        elif fence is not None and not (fence[0] == FENCE and line.startswith("## ")):
            fence[2].append(line)
        elif line.startswith("## "):
            if fence is not None:  # a block no closing fence ended before this heading
                keep_open(entries, fence)
                fence = None
            entries.append({"line": number, "heading": line, "match": HEADING.match(line), "blocks": [],
                            "missing": [], "open": None})
        elif stripped.startswith("```"):
            fence = (stripped[3:].strip(), number, [])
        elif entries and (found := MISSING.match(line.rstrip())):
            entries[-1]["missing"].append(found.group(1).strip())
    if fence is not None and fence[0] == FENCE:
        keep_open(entries, fence)
    return entries


def keep_open(entries: list[dict[str, Any]], fence: tuple[str, int, list[str]]) -> None:
    """Note a `result-contract` fence nothing closed on the entry it sits in; before the first heading it is an
    entry of its own (`preamble`), so the file's own text is held to the one rule that a fence is closed."""
    if entries:
        entries[-1]["open"] = fence[1]
    elif fence[0] == FENCE:
        entries.append({"line": fence[1], "heading": f"```{FENCE}", "match": None, "blocks": [], "missing": [],
                        "open": fence[1], "preamble": True})


def entry_faults(entry: dict[str, Any]) -> list[str]:
    """What is wrong with the shape of one entry, apart from the fields of its block."""
    if entry.get("preamble"):
        return [f"the {FENCE} fence before the first heading is not closed"]
    if entry["match"] is None:
        return [f"is not {SHAPE}"]
    if entry["open"] is not None:
        return [f"the {FENCE} fence is not closed"]
    blocks, missing = entry["blocks"], entry["missing"]
    if len(blocks) > 1:
        return [f"holds {len(blocks)} {FENCE} blocks; an entry holds one"]
    if blocks and missing:
        return [f"holds both a {FENCE} block and a `- **Missing:**` line; it holds one"]
    if not blocks and not missing:
        return [f"holds neither a {FENCE} block nor a `- **Missing:** <reason>` line"]
    return []


def block_faults(entry: dict[str, Any], known: set[str] | None) -> tuple[list[str], dict[str, Any] | None]:
    """The faults of one entry's block, shape and fields (each `<field>: <fault>`), and the block where it parsed
    to an object. An entry that is a `Missing:` line holds none."""
    if not entry["blocks"]:
        return [], None
    try:
        block = json.loads(entry["blocks"][0][1])
    except ValueError as error:
        return [f"block: the body is not JSON ({error})"], None
    if not isinstance(block, dict):
        return [f"block: the body is {block!r}, not one JSON object"], None
    return ([] if newer(block) else check_block(block, entry["match"].group(2), known)), block


def check_record(text: str, where: str, known: set[str] | None) -> tuple[list[str], list[str], int]:
    """Findings, notes and the count of blocks in one record's text; `where` is its path from the root."""
    findings: list[str] = []
    notes: list[str] = []
    count = 0
    for entry in extract(text):
        at = f"{where}:{entry['line']}: {entry['heading']}"
        shape = entry_faults(entry)
        findings += [f"{at} — {fault}" for fault in shape]
        if shape or not entry["blocks"]:
            continue
        count += 1
        faults, block = block_faults(entry, known)
        findings += [f"{at} — {fault}" for fault in faults]
        if block is not None and newer(block):
            notes.append(f"check-decisions: note: {at} — contract {block['contract']} is newer than this "
                         "checker reads; its fields are not held")
    return findings, notes, count


def blocks_in(text: str) -> tuple[list[str], int | None]:
    """The `result-contract` fences in a hand-back, each as its verbatim text (info line to closing fence), and
    the line of one never closed. Fences with another info string are skipped whole."""
    found: list[str] = []
    lines = text.split("\n")
    start: tuple[str, int] | None = None
    for number, line in enumerate(lines):
        if start is None and line.strip().startswith("```"):
            start = (line.strip()[3:].strip(), number)
        elif start is not None and line.strip() == "```":
            if start[0] == FENCE:
                found.append("\n".join(lines[start[1]:number + 1]) + "\n")
            start = None
    return found, (start[1] + 1 if start is not None and start[0] == FENCE else None)


def append(record: Path, title: str, htype: str, stage: str, text: str, known: set[str] | None,
           now: str) -> list[str]:
    """Append one entry to `record` when the hand-back `text` holds exactly one block and the block passes the
    checks the gate makes; otherwise append nothing and return the faults. `title` heads a file made here."""
    fences, unclosed = blocks_in(text)
    if unclosed is not None:
        return [f"the {FENCE} fence opened on line {unclosed} of the hand-back is not closed"]
    if not fences:
        return [f"no {FENCE} block in the hand-back"]
    if len(fences) > 1:
        return [f"two {FENCE} blocks in the hand-back; it holds one"]
    body = "\n".join(fences[0].split("\n")[1:-2])
    try:
        block = json.loads(body)
    except ValueError as error:
        return [f"block: the body is not JSON ({error})"]
    if not isinstance(block, dict):
        return [f"block: the body is {block!r}, not one JSON object"]
    faults = [] if newer(block) else check_block(block, htype, known)
    if faults:
        return faults
    write(record, title, f"## {now} — {htype} — {stage}\n\n{fences[0]}\n")
    return []


def append_missing(record: Path, title: str, htype: str, stage: str, reason: str, now: str) -> None:
    """Append an entry saying no block was handed back, and why."""
    write(record, title, f"## {now} — {htype} — {stage}\n\n- **Missing:** {reason}\n\n")


def write(record: Path, title: str, entry: str) -> None:
    """Append `entry`; make the file with its title first. Bytes already there are never rewritten."""
    if not record.exists():
        entry = f"# Hand-backs — {title}\n\n{entry}"
    elif not record.read_bytes().endswith(b"\n"):
        entry = "\n\n" + entry
    with open(record, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(entry)


def coverage(stages: list[dict[str, Any]], record: str, known: set[str] | None) -> tuple[list[str], int, int, int]:
    """For each ended stage of a slice's `benchmark.json`, whether the record holds what the stage's delegates
    handed back: the lines to print, how many delegated stages have a passing block, how many were delegated and
    how many the harness could not attribute (`usage.source` null: counted as neither). A block belongs to a stage
    when its heading names the stage and its time lies in the stage's `[started, ended]`."""
    entries = [entry for entry in extract(record) if entry["match"] is not None and not entry_faults(entry)]
    lines: list[str] = []
    held = delegated = unattributed = 0
    for stage in stages:
        usage = stage.get("usage")
        if "ended" not in stage:
            continue
        name, started = stage["stage"], stage.get("started", "")
        if usage is not None and not usage.get("source"):
            unattributed += 1
            lines.append(f"hand-backs: {name} {started}: the harness could not attribute its delegates — not counted")
            continue
        if not stage.get("delegated"):
            continue
        delegated += 1
        mine = [entry for entry in entries
                if entry["match"].group(3) == name and started <= entry["match"].group(1) <= str(stage["ended"])]
        passing = [entry for entry in mine if entry["blocks"] and not block_faults(entry, known)[0]]
        if passing:
            held += 1
            lines.append(f"hand-backs: {name} {started} {passing[0]['match'].group(2)}: block")
        elif any(entry["missing"] for entry in mine):
            reason = next(entry["missing"][0] for entry in mine if entry["missing"])
            lines.append(f"hand-backs: {name} {started}: missing — {reason}")
        else:
            lines.append(f"hand-backs: {name} {started}: nothing recorded — a finding for {name}")
    return lines, held, delegated, unattributed
