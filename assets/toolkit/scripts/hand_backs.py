"""The result-contract block a delegate hands back, and the record it is appended to (ADR 0006, D134).

`docs/result-contract.md` is the shape in words; this is the same shape as code, so the gate and the dispatching
session hold a block to one function. Loaded by path, with bytecode off, by `check-decisions.py`; nothing here
prints or exits. A record is `hand-backs.md`: a preamble, then entries `## <UTC time> — drive-<name> — <stage>`
with an optional ` — <started>` (the `started` of the benchmark entry the entry answers, D160), each holding one
fenced `result-contract` block.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NamedTuple

SCHEMA = 1
FENCE = "result-contract"
INSTANT = r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ"
HEADING = re.compile(rf"^## ({INSTANT}) — (drive-[a-z]+) — ([a-z][a-z0-9-]*)(?: — ({INSTANT}))?$")

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


def shown(value: object) -> str:
    """`value` as a fault quotes it: its repr, cut short, and never a traceback for a value nested too deep to print."""
    try:
        text = repr(value)
    except RecursionError:
        return "<nested too deeply to show>"
    return text if len(text) <= 80 else text[:77] + "..."


def text_fault(value: object) -> str | None:
    if not isinstance(value, str):
        return f"{shown(value)} is not a string"
    return None if value.strip() else "is empty; it says something"


def list_fault(value: object) -> str | None:
    if not isinstance(value, list):
        return f"{shown(value)} is not a list of strings"
    odd = [item for item in value if not isinstance(item, str)]
    return f"{shown(odd[0])} is not a string; every item of the list is one" if odd else None


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
        return f"{shown(value)} is not an object of exactly `score` and `reason`; it {shape}"
    score, reason = value["score"], value["reason"]
    if not whole(score) or not 1 <= score <= 5 or not isinstance(reason, str) or not reason.strip():
        return f"{shown(value)} is not valid; it {shape}"
    return None


DECISION = re.compile(r"^## D(\d+) — ", re.M)


def decision_ids(feature: Path) -> set[str]:
    """The `D<n>` ids a feature's decisions.md has a heading for (none where it has no log): the one reading the
    gate, `--hand-back`, `--hand-backs` and the benchmark's count all hold a block's `decisions` to."""
    log = feature / "decisions.md"
    if not log.is_file():
        return set()
    return {f"D{number}" for number in DECISION.findall(log.read_text(encoding="utf-8", errors="replace"))}


def decision_fault(item: object, known: set[str] | None) -> str | None:
    if not isinstance(item, str) or not re.fullmatch(r"D[0-9]+", item):
        return f"{shown(item)} is not a decision id `D<n>`"
    if known is not None and item not in known:
        return f"{shown(item)} names no `## {item} — ` entry in the feature's decisions.md"
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
        return [] if whole(value) and value == SCHEMA else [f"{shown(value)} is not the integer {SCHEMA}"]
    if name == "delegate":
        if not isinstance(value, str) or value not in STATUSES:
            return [f"{shown(value)} is not one of {', '.join(STATUSES)}"]
        return [] if value == heading_type else [f"{shown(value)} differs from the heading's {heading_type!r}"]
    if name == "status":
        delegate = block.get("delegate")
        allowed = STATUSES.get(delegate, ()) if isinstance(delegate, str) else ()
        return [] if not allowed or value in allowed else [f"{shown(value)} is not one of {', '.join(allowed)}"]
    fault = difficulty_fault(value) if kind == "object" else text_fault(value) if kind == "string" else list_fault(value)
    if fault:
        return [fault]
    return items_faults(name, value, known) if kind == "list" else []  # type: ignore[arg-type]


def check_block(block: object, heading_type: str, known: set[str] | None) -> list[str]:
    """The faults of one parsed block, each `<field>: <fault>`; `known` is the feature's `D<n>` ids."""
    if not isinstance(block, dict):
        return [f"block: {shown(block)} is not a JSON object"]
    faults: list[str] = []
    for name, kind in FIELDS:
        if name not in block:
            faults.append(f"{name}: absent; the block holds all {len(FIELDS)} fields")
            continue
        faults += [f"{name}: {fault}" for fault in field_faults(name, kind, block[name], block, heading_type, known)]
    return faults


MISSING = re.compile(r"^- \*\*Missing:\*\* (\S.*)$")
SHAPE = "a heading `## <UTC time> — <drive-type> — <stage>` or `## <UTC time> — <drive-type> — <stage> — <started>`"


OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def opening(line: str) -> tuple[str, int, str] | None:
    """The fence a line opens, CommonMark's way: up to three spaces, then a run of three or more backticks or tildes
    and an info string (which holds no backtick after a backtick run): (character, run length, info string)."""
    found = OPEN.match(line.rstrip("\r"))
    if found is None or (found.group(1)[0] == "`" and "`" in found.group(2)):
        return None
    return found.group(1)[0], len(found.group(1)), found.group(2).strip()


def closes(line: str, char: str, length: int) -> bool:
    """Whether a line closes a fence of `length` runs of `char`: the same character, at least as many, nothing after."""
    return re.fullmatch(rf" {{0,3}}{re.escape(char)}{{{length},}}[ \t]*", line.rstrip("\r")) is not None


def extract(text: str) -> list[dict[str, Any]]:
    """The entries of a record, each `line`, `heading`, `match` (the heading's parts or None), `blocks` (the
    (line, body) of each top-level `result-contract` fence), `missing` (the reasons of `- **Missing:**` lines), `open`
    (the line of a `result-contract` fence no closing fence ended before the next heading), `hidden` (the (fence line,
    heading line) of each entry heading that sits inside another fence) and `foreign` (the (line, info) of a fence of
    another kind never closed). Fences pair CommonMark's way, and one with another info string is skipped whole, quoted
    text; text before the first heading is the file's own."""
    entries: list[dict[str, Any]] = []
    fence: tuple[str, int, str, int, list[str]] | None = None  # character, length, info string, line, body so far
    for number, line in enumerate(text.split("\n"), 1):
        if fence is not None:
            if closes(line, fence[0], fence[1]):
                if fence[2] == FENCE and entries:
                    entries[-1]["blocks"].append((fence[3], "\n".join(fence[4])))
                fence = None
                continue
            if fence[2] != FENCE or not line.startswith("## "):
                fence[4].append(line)
                if fence[2] != FENCE and HEADING.match(line.rstrip("\r")):
                    target(entries, fence)["hidden"].append((fence[3], number))
                continue
            keep_open(entries, fence)  # a block no closing fence ended before this heading
            fence = None
        if line.startswith("## "):
            entries.append({"line": number, "heading": line, "match": HEADING.match(line), "blocks": [],
                            "missing": [], "open": None, "hidden": [], "foreign": None})
        elif (start := opening(line)) is not None:
            fence = (start[0], start[1], start[2], number, [])
        elif entries and (found := MISSING.match(line.rstrip())):
            entries[-1]["missing"].append(found.group(1).strip())
    if fence is not None:
        if fence[2] == FENCE:
            keep_open(entries, fence)
        else:
            target(entries, fence)["foreign"] = (fence[3], fence[2])
    return entries


def target(entries: list[dict[str, Any]], fence: tuple[str, int, str, int, list[str]]) -> dict[str, Any]:
    """The entry a fence belongs to: the last one; before the first heading, an entry of its own (`preamble`), so the
    file's own text is held to the rules that a fence is closed and hides no heading."""
    if not entries:
        entries.append({"line": fence[3], "heading": fence[0] * 3 + fence[2], "match": None, "blocks": [],
                        "missing": [], "open": None, "hidden": [], "foreign": None, "preamble": True})
    return entries[-1]


def keep_open(entries: list[dict[str, Any]], fence: tuple[str, int, str, int, list[str]]) -> None:
    """Note a `result-contract` fence nothing closed on the entry it sits in."""
    target(entries, fence)["open"] = fence[3]


def entry_faults(entry: dict[str, Any]) -> list[str]:
    """What is wrong with the shape of one entry, apart from the fields of its block."""
    hidden = [f"the heading on line {heading} sits inside the fence opened on line {fence}, which hides it"
              for fence, heading in entry["hidden"]]
    if entry["foreign"] is not None:
        hidden.append(f"the {entry['foreign'][1] or 'unlabelled'} fence opened on line {entry['foreign'][0]} "
                      "is not closed")
    if entry.get("preamble"):
        opened = [f"the {FENCE} fence before the first heading is not closed"] if entry["open"] is not None else []
        return hidden + opened
    if entry["match"] is None:
        return [f"is not {SHAPE}"]
    if hidden:
        return hidden
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


DEEP = "block: the body is nested too deeply to read"


def block_faults(entry: dict[str, Any], known: set[str] | None) -> tuple[list[str], dict[str, Any] | None]:
    """The faults of one entry's block, shape and fields (each `<field>: <fault>`), and the block where it parsed
    to an object. An entry that is a `Missing:` line holds none."""
    if not entry["blocks"]:
        return [], None
    try:
        block = json.loads(entry["blocks"][0][1])
    except RecursionError:
        return [DEEP], None
    except ValueError as error:
        return [f"block: the body is not JSON ({error})"], None
    if not isinstance(block, dict):
        return [f"block: the body is {shown(block)}, not one JSON object"], None
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
    """The top-level `result-contract` fences in a hand-back, each as its verbatim text (info line to closing fence),
    and the line of one never closed. Fences pair CommonMark's way, tildes included, and one with another info string
    holds whatever it quotes, a `result-contract` example among it."""
    found: list[str] = []
    lines = text.split("\n")
    start: tuple[str, int, str, int] | None = None  # character, length, info string, index of the opening line
    for number, line in enumerate(lines):
        if start is None:
            if (opened := opening(line)) is not None:
                start = (opened[0], opened[1], opened[2], number)
        elif closes(line, start[0], start[1]):
            if start[2] == FENCE:
                found.append("\n".join(lines[start[3]:number + 1]) + "\n")
            start = None
    return found, (start[3] + 1 if start is not None and start[2] == FENCE else None)


def unix(text: str) -> str:
    """`text` with every line end a newline and none at the end: the record is read with universal newlines and a
    hand-back is not, so a retry of one with CRLF line ends compares as the same."""
    return re.sub(r"\r\n?", "\n", text).rstrip("\n")


def repeats(record: Path, htype: str, stage: str, started: str | None, body: str | None,
            reason: str | None = None) -> bool:
    """Whether the record's last entry for this type, stage and `started` already holds this block (`body`, byte for
    byte) or this reason: a retry of a write that went through. A different one, or the same after another, or the
    same for another start of the stage, is not."""
    if not record.is_file():
        return False
    same = [entry for entry in extract(record.read_text(encoding="utf-8"))
            if entry["match"] is not None and entry["match"].group(2) == htype and entry["match"].group(3) == stage
            and entry["match"].group(4) == started]
    if not same:
        return False
    last = same[-1]
    if body is not None:
        same_text = len(last["blocks"]) == 1 and unix(last["blocks"][0][1]) == unix(body)
        return same_text and not last["missing"]
    return not last["blocks"] and last["missing"][:1] == [reason]


def heading(now: str, htype: str, stage: str, started: str | None) -> str:
    return f"## {now} — {htype} — {stage}" + (f" — {started}" if started else "")


def stage_fault(stage: object) -> str | None:
    """Why one entry of a `benchmark.json`'s `stages` is not a stage this module can read; a missing `started` is
    read as *could not tell*, not refused."""
    if not isinstance(stage, dict) or not isinstance(stage.get("stage"), str) or not stage["stage"]:
        return f"{shown(stage)} is not an object with a `stage` name"
    if stage.get("usage") is not None and not isinstance(stage["usage"], dict):
        return f"the `usage` of {stage['stage']} is not an object"
    return None


def stages_fault(stages: object) -> str | None:
    """Why `stages` is not a list of readable stages, or None."""
    if not isinstance(stages, list):
        return "`stages` is not a list"
    return next((fault for fault in map(stage_fault, stages) if fault), None)


def read_benchmark(bench: Path) -> tuple[list[dict[str, Any]], str | None]:
    """The stages of a slice's `benchmark.json` (none where there is no file) and, where the file cannot be read as a
    benchmark record, one line saying why."""
    if not bench.is_file():
        return [], None
    try:
        data = json.loads(bench.read_text(encoding="utf-8"))
    except UnicodeDecodeError as error:
        return [], f"not UTF-8 ({error.reason} at byte {error.start})"
    except RecursionError:
        return [], "nested too deeply to read"
    except (ValueError, OSError) as error:
        return [], f"not JSON ({error})"
    if not isinstance(data, dict):
        return [], "not a JSON object"
    fault = stages_fault(data.get("stages", []))
    return ([], fault) if fault else (data.get("stages", []), None)


def resolve_started(bench: Path, stage: str, given: str | None,
                    label: str | None = None) -> tuple[str | None, str | None, str | None]:
    """The `started` an entry for `stage` records, a refusal (one line) and a note (D160). `given` is the instant
    passed with `--started`: it must be the start of an entry of that stage. Without it the one open entry of the
    stage is answered; entries but none open are refused, never guessed; no entry at all records none, with a note."""
    stages, fault = read_benchmark(bench)
    if fault:
        return None, f"{label or bench.name} is damaged: {fault}", None
    named = [entry for entry in stages if entry.get("stage") == stage]
    if given is not None:
        if any(entry.get("started") == given for entry in named):
            return given, None, None
        return None, f"{bench.name} has no {stage} entry started at {given}; --started names the start of one", None
    opened = [entry for entry in named if "ended" not in entry and entry.get("started")]
    if opened:
        return str(opened[-1]["started"]), None, None
    if named:
        return None, (f"every {stage} entry in {bench.name} has ended; pass --started with the instant the "
                      "--hand-backs line names"), None
    return None, None, "this entry answers no benchmark entry; --hand-backs will not count it"


def append(record: Path, title: str, htype: str, stage: str, text: str, known: set[str] | None,
           now: str, started: str | None = None) -> tuple[list[str], bool]:
    """Append one entry to `record` when the hand-back `text` holds exactly one block and the block passes the
    checks the gate makes; otherwise append nothing and return the faults. `title` heads a file made here. The
    second item is whether anything was written: a block the record's last entry for this type and stage already
    holds (for this `started`) is a retry, and writes nothing."""
    fences, unclosed = blocks_in(text)
    if unclosed is not None:
        return [f"the {FENCE} fence opened on line {unclosed} of the hand-back is not closed"], False
    if not fences:
        return [f"no {FENCE} block in the hand-back"], False
    if len(fences) > 1:
        return [f"two {FENCE} blocks in the hand-back; it holds one"], False
    body = "\n".join(fences[0].split("\n")[1:-2])
    try:
        block = json.loads(body)
    except RecursionError:
        return [DEEP], False
    except ValueError as error:
        return [f"block: the body is not JSON ({error})"], False
    if not isinstance(block, dict):
        return [f"block: the body is {shown(block)}, not one JSON object"], False
    contract = block.get("contract")
    if whole(contract) and contract != SCHEMA:  # the gate reads a newer record forward; this verb vouches for no other
        return [f"contract: {contract} is not a contract this checker can check (it checks {SCHEMA}); "
                f"hand back a contract {SCHEMA} block"], False
    faults = check_block(block, htype, known)
    if faults:
        return faults, False
    if repeats(record, htype, stage, started, body):
        return [], False
    write(record, title, f"{heading(now, htype, stage, started)}\n\n{fences[0]}\n")
    return [], True


def line_fault(value: str) -> str | None:
    """Why `value` is not one line of printable text, which is all a verb writes outside the delegate's verbatim block
    (the reason of a `Missing:` entry): a line break of any kind, or a control or separator character, would let it
    forge or hide an entry in an append-only record (A1)."""
    odd = next((char for char in value if not char.isprintable()), None)
    return None if odd is None else f"contains {odd!r}, which is not printable"


def append_missing(record: Path, title: str, htype: str, stage: str, reason: str, now: str,
                   started: str | None = None) -> bool:
    """Append an entry saying no block was handed back, and why; False when the record's last entry for this type
    stage and `started` already says exactly this (a retry)."""
    fault = line_fault(reason)
    if fault:
        raise ValueError(f"the reason {fault}")
    if repeats(record, htype, stage, started, None, reason):
        return False
    write(record, title, f"{heading(now, htype, stage, started)}\n\n- **Missing:** {reason}\n\n")
    return True


def write(record: Path, title: str, entry: str) -> None:
    """Append `entry`; make the file with its title first. Bytes already there are never rewritten."""
    if not record.exists():
        entry = f"# Hand-backs — {title}\n\n{entry}"
    elif not record.read_bytes().endswith(b"\n"):
        entry = "\n\n" + entry
    with open(record, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(entry)


# Which stage of `benchmark.json` each delegate type's block belongs to (a copy of `agents/benchmark.py`'s `OWNERS`,
# which a test holds equal). `drive-slice` is not here: inside its worktree its own block goes to the feature record
# (plan.md Q2), so no slice-level stage owes one, and untyped helpers (Explore, general-purpose) owe none.
OWNERS: dict[str, tuple[str, ...]] = {
    "drive-implement": ("implement",), "drive-converge": ("converge",), "drive-gaps": ("gaps",),
    "drive-adversary": ("adversary",), "drive-mutation": ("mutation",), "drive-tasks": ("tasks",),
    "drive-hand": ("demo", "hand"), "drive-skipper": ("skipper",), "drive-bosun": ("bosun",),
}


# The benchmark entry's key for the types that ran. Also the name of a directory at a project's root, so the verify-scoped
# table's test lists it under `NOT_AN_INPUT`: a key of a stage, never a path check-decisions reads.
AGENTS = "agents"


def owed(stage: dict[str, Any]) -> list[str]:
    """The delegate types that ran in an ended stage and owe it a block: typed `drive-*` ones that belong to it."""
    return [agent for agent in stage.get(AGENTS) or [] if stage["stage"] in OWNERS.get(agent, ())]


class Arrival(NamedTuple):
    """When this module reached the project (D161): `at` is the author time of the earliest commit that added it, with
    that commit's short id and date; where git cannot tell, `at` is None and `why` says what stops it."""
    at: datetime | None
    short: str = ""
    date: str = ""
    why: str = ""


def git_out(directory: Path, *args: str) -> str | None:
    """`git <args>` run in `directory`, its stdout; None where git is not there or refuses."""
    try:
        done = subprocess.run(["git", "-C", str(directory), *args], capture_output=True, text=True, check=False,
                              env={**os.environ, "LC_ALL": "C", "GIT_OPTIONAL_LOCKS": "0"})
    except OSError:
        return None
    return done.stdout if done.returncode == 0 else None


def contract_arrived(module: Path | None = None) -> Arrival:
    """The arrival of `module` (default: this file): one `git log --diff-filter=A` for the commits that added it,
    the earliest by author time, since a rebase moves the committer time later and would excuse more stages. The path
    is taken from the git top level, so every layout works without a list of them. Where git cannot say — no git, not
    a repository, a shallow clone (its earliest visible commit can look later than it was), a module no commit has
    added — `at` is None and `why` is the reason. Reads git and writes nothing."""
    path = (module or Path(__file__)).resolve()
    top = git_out(path.parent, "rev-parse", "--show-toplevel")
    if top is None:
        return Arrival(None, why="git is not on the PATH or this is not a repository it can read")
    if (git_out(path.parent, "rev-parse", "--is-shallow-repository") or "").strip() == "true":
        return Arrival(None, why="this is a shallow clone, so the first commit git can see may not be the first")
    root = Path(top.strip()).resolve()
    relative = path.relative_to(root).as_posix()
    log = git_out(root, "log", "--diff-filter=A", "--format=%at%x09%h%x09%aI", "--", relative)
    commits = [line.split("\t") for line in (log or "").splitlines() if line.count("\t") == 2]
    if not commits:
        return Arrival(None, why=f"no commit has added {path.name} yet: commit what slipwai migrate wrote, "
                                 "and this can tell")
    seconds, short, when = min(commits, key=lambda commit: int(commit[0]))
    return Arrival(datetime.fromtimestamp(int(seconds), timezone.utc), short, when[:10])


def instant(value: object) -> datetime | None:
    """A `YYYY-MM-DDTHH:MM:SSZ` string as a UTC instant; None for anything else."""
    if not isinstance(value, str) or not re.fullmatch(INSTANT, value):
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


class Coverage(NamedTuple):
    """`lines` to print; `held` stages with a passing block of `delegated` that owe one; `unattributed` stages whose
    delegates could not be read, `predates` that ended before the contract arrived and `untold` where it could not be
    told whether they did (each said once and counted as neither owed nor held)."""
    lines: list[str]
    held: int
    delegated: int
    unattributed: int
    predates: int = 0
    untold: int = 0


def cut_off(stage: dict[str, Any], arrived: Arrival | None) -> tuple[str, str] | None:
    """For a stage that would owe or be listed: `("predates", line)` where it ended strictly before the arrival,
    `("untold", line)` where that cannot be told, None where it owes as before (also when no arrival was asked for)."""
    if arrived is None:
        return None
    if arrived.at is None:
        return "untold", f"could not tell whether it predates the result contract ({arrived.why}) — not counted"
    ended = instant(stage.get("ended"))
    if ended is None:
        return "untold", ("could not tell whether it predates the result contract (its ended instant "
                          f"{stage.get('ended')!r} does not parse) — not counted")
    if ended < arrived.at:
        return "predates", f"predates the result contract ({arrived.short}, {arrived.date}) — owes nothing"
    return None


def named_types(stage: dict[str, Any]) -> list[str]:
    """The typed delegates the stage names as having run, by `agents` or by the `agent` signal its host reported."""
    signalled = (stage.get("signals") or {}).get("agent")
    return [agent for agent in [*(stage.get(AGENTS) or []), signalled]
            if isinstance(agent, str) and stage["stage"] in OWNERS.get(agent, ())]


def attributable(stage: dict[str, Any]) -> bool:
    """Whether the harness's reading names the stage's delegates: it read a usage, the stage's `agents` are recorded
    where a delegate ran, and a harness whose reader returns no sub-agents at all (Codex) does not hide a typed
    delegate the stage names: `delegated` is false there for every stage, so it cannot say none ran (A3)."""
    usage = stage.get("usage")
    if usage is not None and not usage.get("source"):
        return False
    if stage.get("delegated") and not stage.get(AGENTS):
        return False
    return not (usage is not None and usage["source"] != "claude" and not stage.get("delegated")
                and bool(named_types(stage)))


def coverage(stages: list[dict[str, Any]], record: str, known: set[str] | None,
             arrived: Arrival | None = None) -> Coverage:
    """For each ended stage of a slice's `benchmark.json`, whether the record holds what the stage's delegates
    handed back: the lines to print, how many stages that owe a block have a passing one, how many owe one and how
    many could not be attributed (no usage read, delegated with no agent types recorded, or a harness that reads no
    sub-agents yet names a typed delegate: counted as neither, said once). A stage owes a block when a typed delegate
    that belongs to it ran (`owed`); one that only started untyped helpers, or `drive-slice`, owes this record nothing
    and is not listed. A stage that ended strictly before `arrived` (`contract_arrived`, read by the caller so this
    stays pure) owes nothing and is said to predate the contract; where the arrival could not be told, the stage is
    said and not counted. A block belongs to a stage when its heading names the stage and one of the types that owe it
    and the `started` of its heading is the stage's own (D160)."""
    entries = [entry for entry in extract(record) if entry["match"] is not None and not entry_faults(entry)]
    lines: list[str] = []
    held = delegated = unattributed = predates = untold = 0
    for stage in stages:
        if "ended" not in stage:
            continue
        name, started = stage["stage"], stage.get("started")
        types = owed(stage)
        unreadable = not attributable(stage)
        if not unreadable and (not stage.get("delegated") or not types):
            continue
        cut = cut_off(stage, arrived)
        if cut is None and instant(started) is None:  # no start to match an entry to, and never a window from time 0
            cut = "untold", "could not tell which entries answer it (no started instant) — not counted"
            started = "?"
        if cut is not None:
            predates += cut[0] == "predates"
            untold += cut[0] == "untold"
            lines.append(f"hand-backs: {name} {started or '?'}: {cut[1]}")
            continue
        if unreadable:
            unattributed += 1
            lines.append(f"hand-backs: {name} {started}: the harness could not attribute its delegates — not counted")
            continue
        delegated += 1
        mine = [entry for entry in entries
                if entry["match"].group(3) == name and entry["match"].group(2) in types
                and entry["match"].group(4) == started]
        checked = [(entry, *block_faults(entry, known)) for entry in mine if entry["blocks"]]
        passing = [entry for entry, faults, block in checked if not faults and not newer(block)]
        later = [block["contract"] for _, _, block in checked if newer(block)]
        if passing:
            held += 1
            lines.append(f"hand-backs: {name} {started} {passing[0]['match'].group(2)}: block")
        elif later:  # a block is there and nothing here can check it: information, not a finding
            lines.append(f"hand-backs: {name} {started} {', '.join(types)}: block of contract {later[0]} — "
                         "this factory cannot check it; not counted as held")
        elif any(entry["missing"] for entry in mine):
            reason = next(entry["missing"][0] for entry in mine if entry["missing"])
            lines.append(f"hand-backs: {name} {started} {', '.join(types)}: missing — {reason}")
        else:
            lines.append(f"hand-backs: {name} {started} {', '.join(types)}: nothing recorded — a finding for converge")
    return Coverage(lines, held, delegated, unattributed, predates, untold)
