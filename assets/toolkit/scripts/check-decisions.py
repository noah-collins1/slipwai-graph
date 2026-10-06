#!/usr/bin/env python3
"""Hold `/cruise`'s record to its shape: every decision the run took, and every demo it ran, readable and true.

A run with nobody at the wheel is trusted through what it wrote down. `specs/<feature>/decisions.md` is the one
place every product decision the machine took can be read and overturned, and `specs/<feature>/slices/<id>/
demo-log.md` is what a person reads to trust an acceptance the machine gave. Both are append-only entries in a
fixed shape — `commands/cruise.md` shows it, and `.specify/product-owner.md` repeats it — and this is the
gate on that shape: an entry with a field missing is a decision nobody can audit, a `Written to` path that is
not in the tree is a decision that was never applied, and evidence that does not exist is no evidence.

What is held, one finding per line (the adversary log's row per finished slice included, because `/adversary` says
an unwritten row is a pass that has to be run again, and until now nothing noticed one):

- a decision entry is `## D<n> — <question>` followed by the fixed fields in order: **Stage** (with Slice, When,
  Iteration), **Question**, **Options**, **Decision**, **Why**, **Decided by**, **Confidence** (with Would
  reverse if), **Written to**, **Status**;
- entries are numbered contiguously from `D1`, in order;
- **Decided by** is `host (stage recommendation)`, `host (standing decision D<m>)`, `drive-skipper (<model>)`,
  `drive-bosun` — with or without its `(<model>)` — or `human`; **Status** is `standing`, `overridden by D<m>` or `overridden by human <date>`;
- every **Written to** path exists in the repository, and a path still carrying `<placeholders>` is a finding;
- a demo entry is `## <instant> — <verdict> · iteration <n> · drive-hand (<model>)`, its verdict one of
  `accepted`, `behaviour`, `implementation`, followed by **Started with**, **Driven through**, **Examples**,
  **Evidence**, **Feedback**; every **Evidence** path exists, beside the log or from the root, or is `none`;
- every slice the ladder calls done — a row in `specs/<feature>/slices/README.md`, or `status: implemented` in
  `docs/event-model/model.yaml` — has a `## <slice-id> · …` row in `specs/<feature>/adversary-log.md`: the attack,
  or the recorded skip, that `/adversary` writes after every acceptance. The model is the whole project's, so a
  slice in it counts for the feature its `spec` or `gwt` path is under, or, naming none, the one holding
  `slices/<id>/`; an implemented slice no feature holds is noted, not charged to every feature.

`python3 scripts/check-decisions.py --scope <slice-id> [--feature <name>]` prints, verbatim and in number order, the
standing decisions a slice's later decisions must agree with: the entries whose `- **Scope:**` line names the slice
(two ids meet when their heads are equal — the letters, case set aside, and the number, read as a number — whatever
the slug, so `S02`, `S2` and `s02-runner` meet `S02-runner-bookkeeping` and `S1` does not meet `S12-…`), the ones that
say `global`, and the ones with no line or no readable one, which are carried as global because a filter that could
hide a binding decision is the wrong one. A value is unreadable when it is not `global` alone or a list of single
ASCII ids (`S01-S03` is two ids, not one), and an entry that says its `Scope:` or its `Status:` on more than one line
is unreadable whole: the verb carries it as global. The gate refuses a second `Scope:` line, which is new with that
line, naming the entry; a second `Status:` line it only notes (`check-decisions: note:`, exit code unchanged), because a
log written before this release can hold one and the gate does not newly refuse what an earlier checker passed. For a log
with no `Scope:` line the gate answers exactly as the checker before it did, a byte-order mark included. It ends with one line of counts, names
each overridden entry with what overrode it, writes nothing, and needs `--feature` only when `specs/` holds more
than one `decisions.md`.

A call it does not understand is usage and exit 2, never a run of something else: `--scope` wants an id of upper-case
letters and a number, `--feature` a name, each once, and `--help` prints the usage and exits 0. A block under a `##`
heading it cannot read as `## D<n> — <question>` is printed in its place and counted as carried for want of a heading it can read, and the verb then exits 1 saying the log does not pass. A
log that is not UTF-8 is one line naming the file and exit 1, for the gate and for the verb alike. The verb reads past a byte-order mark at the start of the log, so its first entry is
printed and counted as an entry; the gate does not.

`python3 scripts/check-decisions.py --adversary-baseline` is for a project that migrated across that last rule: it
writes, once, a `## <id> · predates the adversary gate · <date>` row for every done slice without one, which the gate accepts
and which says the slice was never attacked. A second baseline is refused.

Every `specs/<feature>/hand-backs.md` and `specs/<feature>/slices/<id>/hand-backs.md` is held to the result-contract
shape `docs/result-contract.md` writes down: an entry `## <UTC time> — drive-<name> — <stage>` holding one fenced
`result-contract` block, or a `- **Missing:** <reason>` line, one finding per fault naming the file, the heading and
the field. The shape itself lives in `hand_backs.py` beside this script. Where no such record exists the gate says and
does exactly what it did before them; where one does, its summary gains `, <n> hand-back(s) in <m> record(s)`.

A project with no record anywhere passes and says so: the gate runs in `make verify` from the first commit.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


def project_root(script: Path, depth: int) -> Path:
    for candidate in script.parents:
        if (candidate / "project.json").is_file():
            return candidate
    return script.parents[depth]


ROOT = project_root(Path(__file__).resolve(), 1)
SPECS = ROOT / "specs"
DECISIONS = "decisions.md"
DEMO_LOG = "demo-log.md"
ADVERSARY_LOG = "adversary-log.md"
HAND_BACKS = "hand-backs.md"
# The fields of one decision entry, in order, as the bold label each line opens with.
DECISION_FIELDS = ("Stage", "Question", "Options", "Decision", "Why", "Decided by", "Confidence", "Written to",
                   "Status")
DEMO_FIELDS = ("Started with", "Driven through", "Examples", "Evidence", "Feedback")
VERDICTS = ("accepted", "behaviour", "implementation")
DECISION_HEADING = re.compile(r"^## D(\d+) — (.+)$")
DEMO_HEADING = re.compile(r"^## (\S+) — (\w+) · iteration (\d+) · drive-hand \((.+)\)$")
# The bosun's entries name the type alone or with the model, because the command tells it `Decided by: drive-bosun`
# and the skipper's habit of naming its model is one it may share.
DECIDED_BY = re.compile(r"^(host \(stage recommendation\)|host \(standing decision D\d+\)|drive-skipper \(.+\)|"
                        r"drive-bosun( \(.+\))?|human)$")
STATUS = re.compile(r"^(standing|overridden by D\d+|overridden by human \S+)$")
FIELD = re.compile(r"^- \*\*([^*]+):\*\* ?(.*)$")
PLACEHOLDER = re.compile(r"<[^>]*>")
# A slice id as `done_slices()` reads it: the released head, then a slug after `-` or `.` that ends on a letter or digit.
# ASCII only: a digit that is not 0-9 is not a number the filter can compare.
SLICE_ID = re.compile(r"[A-Za-z]+[0-9]+(?![A-Za-z0-9_])(?:[.-][A-Za-z0-9._-]*[A-Za-z0-9])?")
# What `--scope` accepts: the same shape, its letters upper case.
WANTED_ID = re.compile(r"[A-Z]+[0-9]+(?![A-Za-z0-9_])(?:[.-][A-Za-z0-9._-]*[A-Za-z0-9])?")
HEAD = re.compile(r"([A-Za-z]+)([0-9]+)")
USAGE = "usage: check-decisions.py [--scope <slice-id> [--feature <name>] | --adversary-baseline | --help]"


class NotUtf8(Exception):
    """A log the gate reads as text and cannot: said in one line naming the file, never as a traceback."""


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise NotUtf8(f"{path.relative_to(ROOT).as_posix()}: not UTF-8 ({error.reason} at byte {error.start}); "
                      "the gate reads every log as UTF-8 text") from error


class Fields(dict[str, str]):
    """One entry's fields as first label → the rest of the line, and `twice`: the labels a later line said again."""

    def __init__(self) -> None:
        super().__init__()
        self.twice: set[str] = set()


Entry = tuple[int, "re.Match[str] | None", Fields]


def lines_of(text: str) -> list[str]:
    """Lines divided at line feeds only (`read_text` has already made a carriage return one): a form feed or U+2028
    inside a field does not start another one."""
    return text.split("\n")


def decisions_text(path: Path) -> str:
    """A decisions log as the verb reads it, a byte-order mark at the very start read past so the first entry is an
    entry (D65). The gate does not: it reads such a log as the checker before the `Scope:` line did."""
    return read(path).removeprefix("\ufeff")


def pieces(text: str, legacy: bool) -> list[tuple[str, bool]]:
    """The lines of a log, each with whether it begins a line of the log. The verb reads line feeds only, so what it
    prints is what is written; the gate reads as the checker did before the `Scope:` line (`str.splitlines`, which
    also breaks at a form feed, U+2028 or U+0085), so a log it passed it still passes, and takes a `Scope:` label
    only where a line feed began its line."""
    if not legacy:
        return [(line, True) for line in lines_of(text)]
    found, begins = [], True
    for piece in text.splitlines(keepends=True):
        found.append((piece.splitlines()[0], begins))
        begins = piece.endswith("\n")
    return found


def entries(text: str, heading: re.Pattern[str], legacy: bool = False) -> list[Entry]:
    """Each entry as (line number, its heading match or None for a heading in the wrong shape, its fields)."""
    found: list[Entry] = []
    for number, (line, begins) in enumerate(pieces(text, legacy), start=1):
        if line.startswith("## "):
            found.append((number, heading.match(line), Fields()))
        elif found and (field := FIELD.match(line)):
            label = field.group(1).split(":")[0].strip()
            if label == "Scope" and not begins:
                continue
            if label in found[-1][2]:
                found[-1][2].twice.add(label)
            else:
                found[-1][2][label] = field.group(2).strip()
    return found


def paths_of(value: str) -> list[str]:
    """The paths a `Written to` or `Evidence` line names: backticked, or comma-separated bare."""
    quoted = re.findall(r"`([^`]+)`", value)
    if quoted:
        return quoted
    return [part.strip() for part in value.split(",") if part.strip()]


def path_findings(where: str, label: str, value: str, base: Path) -> list[str]:
    findings = []
    for path in paths_of(value):
        if PLACEHOLDER.search(path):
            findings.append(f"{where}: {label} still carries a placeholder: {path}")
        elif not (base / path).exists() and not (ROOT / path).exists():
            findings.append(f"{where}: {label} names `{path}`, which is not in the tree")
    return findings


def scope_tokens(value: str) -> list[str] | None:
    """The slice ids a `Scope:` value lists (backticks tolerated), `["global"]` for the word alone, or None where
    the value is empty or is neither."""
    tokens = [part.strip().strip("`").strip() for part in value.split(",")]
    if tokens == ["global"]:
        return tokens
    if value.strip() and all(SLICE_ID.fullmatch(token) and one_id(token) for token in tokens):
        return tokens
    return None


def one_id(token: str) -> bool:
    """False for a token that carries a second id head after its first (`S01-S03`, `S05-x.S02-y`): letters of the
    first head's and a number, standing alone as a piece of the slug. A slug such as `oauth2` is not one."""
    first = HEAD.match(token)
    assert first is not None
    for piece in re.split(r"[.-]", token)[1:]:
        later = HEAD.fullmatch(piece)
        if later and later.group(1).lower() == first.group(1).lower():
            return False
    return True


def scope_finding(where: str, number: int, value: str) -> list[str]:
    if scope_tokens(value) is not None:
        return []
    return [f"{where}: D{number} `Scope` is {value!r}; it is `global` alone or slice ids separated by commas"]


def scope_notes(path: Path) -> list[str]:
    """One note per entry with no `Scope:` line after an entry that has one (it is carried as global), and one per
    entry that says `Status:` twice (the first is read): a log written before the `Scope:` line can hold the second,
    so the gate says it and does not refuse it (D65)."""
    relative = path.relative_to(ROOT).as_posix()
    notes, seen = [], False
    for line, heading, fields in entries(read(path), DECISION_HEADING, legacy=True):
        if heading is None:
            continue
        if "Status" in fields.twice:
            notes.append(f"check-decisions: note: {relative}:{line}: D{heading.group(1)} has more than one "
                         "`Status:` line; the first is the one read, and the verb carries the entry")
        if "Scope" in fields:
            seen = True
        elif seen:
            notes.append(f"check-decisions: note: {relative}:{line}: D{heading.group(1)} has no `Scope:` line after "
                         "an entry that has one; it is carried as global")
    return notes


def check_decisions(path: Path) -> list[str]:
    relative = path.relative_to(ROOT).as_posix()
    findings: list[str] = []
    expected = 1
    for line, heading, fields in entries(read(path), DECISION_HEADING, legacy=True):
        where = f"{relative}:{line}"
        if heading is None:
            findings.append(f"{where}: a heading that is not `## D<n> — <question>`")
            continue
        number = int(heading.group(1))
        if number != expected:
            findings.append(f"{where}: D{number} where D{expected} was expected — entries are numbered contiguously")
        expected = number + 1
        missing = [field for field in DECISION_FIELDS if field not in fields]
        if missing:
            findings.append(f"{where}: D{number} is missing {', '.join(f'**{field}:**' for field in missing)}")
            continue
        listed = [label for label in fields if label in DECISION_FIELDS]
        if listed != list(DECISION_FIELDS):
            findings.append(f"{where}: D{number}'s fields are out of order; the shape is {', '.join(DECISION_FIELDS)}")
        if not DECIDED_BY.match(fields["Decided by"]):
            findings.append(f"{where}: D{number} `Decided by` is {fields['Decided by']!r}; it is host (stage "
                            "recommendation), host (standing decision D<m>), drive-skipper (<model>), drive-bosun "
                            "or human")
        if not STATUS.match(fields["Status"]):
            findings.append(f"{where}: D{number} `Status` is {fields['Status']!r}; it is standing, overridden by "
                            "D<m> or overridden by human <date>")
        if "Scope" in fields.twice:
            findings.append(f"{where}: D{number} has more than one `Scope:` line; an entry says its scope once")
        if "Scope" in fields:
            findings += scope_finding(where, number, fields["Scope"])
        findings += path_findings(where, f"D{number} `Written to`", fields["Written to"], ROOT)
    return findings


def check_demo_log(path: Path) -> list[str]:
    relative = path.relative_to(ROOT).as_posix()
    findings: list[str] = []
    for line, heading, fields in entries(read(path), DEMO_HEADING, legacy=True):
        where = f"{relative}:{line}"
        if heading is None:
            findings.append(f"{where}: a heading that is not `## <instant> — <verdict> · iteration <n> · drive-hand (<model>)`")
            continue
        verdict = heading.group(2)
        if verdict not in VERDICTS:
            findings.append(f"{where}: verdict {verdict!r} is not one of {', '.join(VERDICTS)}")
        missing = [field for field in DEMO_FIELDS if field not in fields]
        if missing:
            findings.append(f"{where}: the {heading.group(1)} demo is missing "
                            f"{', '.join(f'**{field}:**' for field in missing)}")
            continue
        if fields["Evidence"].strip() != "none":
            findings += path_findings(where, "`Evidence`", fields["Evidence"], path.parent)
    return findings


def implemented() -> list[tuple[str, str | None]]:
    """Every slice `docs/event-model/model.yaml` marks `status: implemented`, with the feature it names: the
    `specs/<feature>/` its `spec` or `gwt` path is under, or None where it names none. The model is the whole
    project's, so a slice in it belongs to one feature, not to every feature that asks."""
    model = ROOT / "docs/event-model/model.yaml"
    found: list[tuple[str, str | None]] = []
    if model.is_file():
        for block in re.split(r"^\s*- id:\s*", read(model), flags=re.M)[1:]:
            ident = block.split("\n", 1)[0].strip().strip("'\"")
            if ident and re.search(r"^\s*status:\s*implemented\s*$", block, re.M):
                named = re.search(r"^\s*(?:spec|gwt):\s*['\"]?specs/([^/\s'\"]+)/", block, re.M)
                found.append((ident, named.group(1) if named else None))
    return found


def done_slices(feature: Path) -> set[str]:
    """The slices this feature has finished, as the ladder marks them (`commands/drive.md`, *Ready-set selection*):
    a row in its register at `slices/README.md`, or `status: implemented` in the event model on a slice that names
    this feature, or names none and has its folder at `slices/<id>/` here."""
    done: set[str] = set()
    register = feature / "slices/README.md"
    if register.is_file():
        for line in read(register).splitlines():
            if line.strip().startswith("|"):
                first = line.strip().strip("|").split("|")[0].strip().strip("`")
                # the released head (letters, digits, a word boundary), then a slug after `-` or `.` that ends on a letter or digit
                found = re.match(r"[A-Za-z]+\d+(?![A-Za-z0-9_])(?:[.-][A-Za-z0-9._-]*[A-Za-z0-9])?", first)
                if found:
                    done.add(found.group(0))
    for ident, named in implemented():
        if named == feature.name or (named is None and (feature / "slices" / ident).is_dir()):
            done.add(ident)
    return done


def lacking_rows(done: set[str], log_text: str) -> list[str]:
    """The done slices the adversary log has no row for: a row is headed with the slice's whole id or with its bare
    prefix (`S00` for `S00-run-path`), which rows written before the id was read whole still use."""
    rows = set(re.findall(r"^## (\S+) · ", log_text, re.M))
    def headed(ident: str) -> bool:
        prefix = re.match(r"[A-Za-z]+\d+", ident)  # an id with no such head has no prefix: looked up whole only
        return ident in rows or (prefix is not None and prefix.group(0) in rows)

    return sorted(ident for ident in done if not headed(ident))


def unowned() -> list[str]:
    """Implemented slices no feature holds: the model names no feature for them and no `specs/*/slices/<id>/`
    exists. Not charged to any feature — said, so the model can be given its `spec` or the id corrected."""
    features = [path for path in (ROOT / "specs").iterdir() if path.is_dir()] if (ROOT / "specs").is_dir() else []
    return sorted(ident for ident, named in implemented()
                  if named is None and not any((feature / "slices" / ident).is_dir() for feature in features))


def check_adversary_rows() -> list[str]:
    """A finished slice with no row in the adversary log was never attacked and never recorded as skipped."""
    findings: list[str] = []
    for feature in sorted(SPECS.iterdir()) if SPECS.is_dir() else []:
        done = done_slices(feature) if (feature / "slices").is_dir() else set()
        if not done:
            continue
        log = feature / ADVERSARY_LOG
        for ident in lacking_rows(done, read(log) if log.is_file() else ""):
            findings.append(f"{log.relative_to(ROOT).as_posix()}: no row for {ident}, which is done — `/adversary` runs "
                            "after every acceptance and records the attack or the skip; an unwritten row is a pass "
                            "that has to be run again")
    return findings


PREDATES = "predates the adversary gate"


def baseline() -> int:
    """Write, once, a row for every done slice the adversary log lacks, saying it was finished before this gate held
    finished slices to the log — which is true, and which no later slice may cite as an attack. For a project that
    migrated across the gate, whose history cannot be attacked honestly after the fact; refused where any log
    already carries a baseline row, so it is the done set at one moment and not a way past the gate afterwards."""
    logs = sorted(SPECS.glob(f"*/{ADVERSARY_LOG}")) if SPECS.is_dir() else []
    taken = [log for log in logs if f"· {PREDATES}" in read(log)]
    if taken:
        print(f"check-decisions: a baseline was already taken ({taken[0].relative_to(ROOT).as_posix()}); a slice "
              "finished since is held to a row `/adversary` writes", file=sys.stderr)
        return 1
    written = 0
    today = date.today().isoformat()
    for feature in sorted(SPECS.iterdir()) if SPECS.is_dir() else []:
        if not (feature / "slices").is_dir():
            continue
        log = feature / ADVERSARY_LOG
        text = read(log) if log.is_file() else f"# Adversary log — {feature.name}\n"
        missing = lacking_rows(done_slices(feature), text)
        if not missing:
            continue
        rows = "".join(f"\n## {ident} · {PREDATES} · {today}\n\nFinished before `check-decisions` held every done "
                       "slice to a row here. Never attacked by `/adversary`, so no slice may cite this row as "
                       "coverage.\n" for ident in missing)
        log.write_text(text.rstrip("\n") + "\n" + rows, encoding="utf-8", newline="\n")
        written += len(missing)
        print(f"check-decisions: {log.relative_to(ROOT).as_posix()}: {len(missing)} baseline row(s)")
    print(f"check-decisions: baselined {written} done slice(s)" if written
          else "check-decisions: every done slice already has a row — nothing to baseline")
    return 0


def meets(wanted: str, named: str) -> bool:
    """Two slice ids meet when their heads are equal: the letters, case set aside, and the number, read as a number
    (compared as digits without their leading zeros, so no length is too long), whatever the slug. `S02`, `S2` and
    `s02-runner` meet `S02-runner-bookkeeping`; `S1` does not meet `S12`."""
    def head(ident: str) -> tuple[str, str] | None:
        found = HEAD.match(ident)
        return (found.group(1).lower(), found.group(2).lstrip("0") or "0") if found else None

    return wanted == named or (head(wanted) is not None and head(wanted) == head(named))


def placed(wanted: str, fields: Fields) -> str:
    """How the filter places one entry: `scope`, `global`, `unlined` (no line, carried as global), or `out`.
    A value it cannot read, and an entry that says its scope or its status twice, is global; it never drops what
    it cannot place."""
    if fields.twice & {"Scope", "Status"}:
        return "global"
    if "Scope" not in fields:
        return "unlined"
    tokens = scope_tokens(fields["Scope"])
    if tokens is None or tokens == ["global"]:
        return "global"
    return "scope" if any(meets(wanted, token) for token in tokens) else "out"


def scope_verb(wanted: str, feature: str | None) -> int:
    logs = sorted(SPECS.glob(f"*/{DECISIONS}")) if SPECS.is_dir() else []
    if feature is not None:
        logs = [log for log in logs if log.parent.name == feature]
    elif len(logs) > 1:
        names = ", ".join(log.parent.name for log in logs)
        print(f"check-decisions: specs/ holds several decisions.md; choose one with --feature <name>: {names}",
              file=sys.stderr)
        return 1
    if not logs:
        print("check-decisions: no decisions.md under specs/" + (f" for feature {feature}" if feature else ""),
              file=sys.stderr)
        return 1
    text = decisions_text(logs[0])
    lines = lines_of(text)
    found = entries(text, DECISION_HEADING)
    count = {"scope": 0, "global": 0, "unlined": 0, "unread": 0, "out": 0}
    overridden: list[str] = []
    for index, (line, heading, fields) in enumerate(found):
        if heading is None:  # a block under a heading it cannot read: carried, never placed, never dropped
            where = "unread"
        else:
            status = STATUS.match(fields.get("Status", "standing"))
            if status and status.group(0).startswith("overridden") and "Status" not in fields.twice:
                overridden.append(f"D{heading.group(1)} ({status.group(0)})")
                continue
            where = placed(wanted, fields)
        count[where] += 1
        if where != "out":
            end = found[index + 1][0] - 1 if index + 1 < len(found) else len(lines)
            print("\n".join(lines[line - 1:end]).rstrip() + "\n")
    carried = count["scope"] + count["global"] + count["unlined"] + count["unread"]
    unread = f", {count['unread']} carried for want of a heading it can read" if count["unread"] else ""
    print(f"check-decisions: carried {carried} of {len(found)} entries for {wanted}: {count['scope']} in scope, "
          f"{count['global']} global, {count['unlined']} carried as global for want of a line{unread}; "
          f"{count['out']} left out as out of scope; overridden and left out: {', '.join(overridden) or 'none'}")
    if count["unread"]:
        print(f"check-decisions: {logs[0].relative_to(ROOT).as_posix()} does not pass check-decisions: "
              f"{count['unread']} block(s) under a heading that is not `## D<n> — <question>`", file=sys.stderr)
        return 1
    return 0


def verb_options(arguments: list[str]) -> dict[str, str] | None:
    """`--scope <slice-id>` and `--feature <name>`, once each, in either order; None for anything else."""
    options: dict[str, str] = {}
    for flag, value in zip(arguments[0::2], arguments[1::2], strict=False):
        if flag not in ("--scope", "--feature") or flag in options or not value or value.startswith("-"):
            return None
        options[flag] = value
    if len(arguments) % 2 or not WANTED_ID.fullmatch(options.get("--scope", "")):
        return None
    return options


def hand_backs_module() -> Any:
    """`hand_backs.py` beside this script, loaded by path with bytecode off (a `__pycache__` under scripts/ would
    make every later scoped run the full gate)."""
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("hand_backs", Path(__file__).resolve().with_name("hand_backs.py"))
    if spec is None or spec.loader is None:
        raise ImportError("cannot load hand_backs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_hand_backs(records: list[Path]) -> tuple[list[str], list[str], int]:
    """The findings, the notes and the count of hand-backs in every record, each finding naming its file."""
    findings: list[str] = []
    if not records:  # no record: the module is not even loaded, and the gate is what it was
        return findings, [], 0
    module = hand_backs_module()
    notes: list[str] = []
    blocks = 0
    for path in records:
        feature = path.parent if path.parent.parent == SPECS else path.parent.parent.parent
        known = module.decision_ids(feature)
        found, said, count = module.check_record(read(path), path.relative_to(ROOT).as_posix(), known)
        findings += found
        notes += said
        blocks += count
    return findings, notes, blocks


def gate() -> int:
    for ident in unowned():
        print(f"check-decisions: note: {ident} is implemented in docs/event-model/model.yaml but names no feature "
              "and has no specs/*/slices/ folder, so no adversary log is asked for it")
    decisions = sorted(SPECS.glob(f"*/{DECISIONS}")) if SPECS.is_dir() else []
    logs = sorted(SPECS.glob(f"*/slices/*/{DEMO_LOG}")) if SPECS.is_dir() else []
    records = sorted([*SPECS.glob(f"*/{HAND_BACKS}"), *SPECS.glob(f"*/slices/*/{HAND_BACKS}")]) if SPECS.is_dir() else []
    findings: list[str] = check_adversary_rows()
    if not decisions and not logs and not records and not findings:
        print("check-decisions: no decisions.md or demo-log.md under specs/ — nothing recorded yet")
        return 0
    for path in decisions:
        for note in scope_notes(path):
            print(note)
        findings += check_decisions(path)
    for path in logs:
        findings += check_demo_log(path)
    held, said, blocks = check_hand_backs(records)
    for note in said:
        print(note)
    findings += held
    if findings:
        print("check-decisions: the record is not in the shape commands/cruise.md shows\n", file=sys.stderr)
        for finding in findings:
            print(f"  {finding}", file=sys.stderr)
        print(file=sys.stderr)
        return 1
    counted = sum(len(entries(read(p), DECISION_HEADING, legacy=True)) for p in decisions)
    demos = sum(len(entries(read(p), DEMO_HEADING, legacy=True)) for p in logs)
    kept = f", {blocks} hand-back(s) in {len(records)} record(s)" if records else ""
    print(f"check-decisions: {counted} decision(s) in {len(decisions)} file(s), {demos} demo(s) in {len(logs)} log(s)"
          f"{kept}, every field present and every path in the tree, every done slice in the adversary log")
    return 0


HAND_USAGE = (
    "usage: check-decisions.py --hand-back <specs/feature[/slices/id]> <drive-type> <stage> [--started <instant>]"
    "   (the hand-back on stdin)\n"
    "       check-decisions.py --hand-back-missing <specs/feature[/slices/id]> <drive-type> <stage>"
    " [--started <instant>] <reason>\n"
    "       check-decisions.py --hand-backs <specs/feature/slices/id>")
FOLDER = re.compile(r"specs/([A-Za-z0-9][A-Za-z0-9._-]*)(?:/slices/([A-Za-z0-9][A-Za-z0-9._-]*))?")


def refuse(reason: str) -> int:
    """Usage, exit 2, led by one line naming the argument that failed."""
    print(f"check-decisions: {reason}", file=sys.stderr)
    print(HAND_USAGE, file=sys.stderr)
    return 2


def folder_of(argument: str, slice_only: bool) -> tuple[str, re.Match[str] | None, str]:
    """The folder an argument names, without a leading `./` or a trailing `/`; its `FOLDER` match; and, where it is
    not a folder the verb takes, why."""
    path = argument
    while path.startswith("./"):
        path = path[2:]
    path = path.rstrip("/")
    found = FOLDER.fullmatch(path)
    if found is None or (slice_only and not found.group(2)):
        want = "specs/<feature>/slices/<id>" if slice_only else "specs/<feature> or specs/<feature>/slices/<id>"
        return path, None, f"folder {argument!r} is not {want}"
    if not (ROOT / path).is_dir():
        return path, None, f"folder {argument!r} does not exist"
    return path, found, ""


def hand_back_verb(arguments: list[str]) -> int:
    """`--hand-back` and `--hand-back-missing`: append one entry to the record under a feature or a slice. Usage
    (exit 2, with a line naming the argument) unless the folder is `specs/<feature>` or `specs/<feature>/slices/<id>`
    and exists, the type is one of the ten and the stage is a lower-case word."""
    module = hand_backs_module()
    missing = arguments[0] == "--hand-back-missing"
    started: str | None = None
    if len(arguments) > 4 and arguments[4] == "--started":
        if len(arguments) < 6 or not re.fullmatch(module.INSTANT, arguments[5]):
            return refuse("--started takes an instant `YYYY-MM-DDTHH:MM:SSZ`")
        started = arguments[5]
        arguments = arguments[:4] + arguments[6:]
    wanted = 5 if missing else 4
    if len(arguments) < wanted or (not missing and len(arguments) != wanted):
        return refuse(f"{len(arguments) - 1} argument(s) given; {arguments[0]} takes {wanted - 1}")
    where, folder, why = folder_of(arguments[1], False)
    if folder is None:
        return refuse(why)
    if arguments[2] not in module.STATUSES:
        return refuse(f"type {arguments[2]!r} is not one of the ten drive-* delegate types")
    if not re.fullmatch(r"[a-z][a-z0-9-]*", arguments[3]):
        return refuse(f"stage {arguments[3]!r} is not a lower-case word (a-z, 0-9, -; no underscore)")
    if missing and not " ".join(arguments[4:]).strip():
        return refuse("the reason is empty; --hand-back-missing says why")
    fault = module.line_fault(" ".join(arguments[4:])) if missing else None
    if fault:
        return refuse(f"the reason {fault}; it is one line of printable text, so keep the first line of the "
                      "delegate's words")
    record = ROOT / where / HAND_BACKS
    title = folder.group(2) or folder.group(1)
    started, refusal, note = module.resolve_started(ROOT / where / "benchmark.json", arguments[3], started)
    if refusal:
        print(f"check-decisions: {refusal}", file=sys.stderr)
        return 1
    if note:
        print(f"check-decisions: note: {note}", file=sys.stderr)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if missing:
        wrote = module.append_missing(record, title, arguments[2], arguments[3], " ".join(arguments[4:]).strip(), now,
                                     started)
        faults: list[str] = []
    else:
        faults, wrote = module.append(record, title, arguments[2], arguments[3], sys.stdin.read(),
                                      module.decision_ids(ROOT / "specs" / folder.group(1)), now,
                                      started)
    for fault in faults:
        print(f"check-decisions: {fault}", file=sys.stderr)
    if not faults and not wrote:
        print(f"check-decisions: note: {where}/{HAND_BACKS} already ends this {arguments[2]} {arguments[3]} "
              "entry with the same content; nothing appended", file=sys.stderr)
    return 1 if faults else 0


def coverage_verb(arguments: list[str]) -> int:
    """`--hand-backs <specs/feature/slices/id>`: for each ended stage of the slice's benchmark.json the transcript
    shows was delegated, whether the record holds a passing block for it. A reading, not a gate: exit 0."""
    if len(arguments) != 2:
        return refuse(f"{len(arguments) - 1} argument(s) given; --hand-backs takes 1")
    path, folder, why = folder_of(arguments[1], True)
    if folder is None:
        return refuse(why)
    where = ROOT / path
    bench = where / "benchmark.json"
    stages = json.loads(bench.read_text(encoding="utf-8")).get("stages", []) if bench.is_file() else []
    record = where / HAND_BACKS
    module = hand_backs_module()
    lines, held, delegated, _ = module.coverage(
        stages, read(record) if record.is_file() else "", module.decision_ids(ROOT / "specs" / folder.group(1)))
    for line in lines:
        print(line)
    print(f"hand-backs: with a result contract: {held} of {delegated}")
    return 0


def main() -> int:
    arguments = sys.argv[1:]
    if not arguments:
        return gate()
    if arguments == ["--help"]:
        print(USAGE)
        return 0
    if arguments == ["--adversary-baseline"]:
        return baseline()
    if arguments[0] in ("--hand-back", "--hand-back-missing"):
        return hand_back_verb(arguments)
    if arguments[0] == "--hand-backs":
        return coverage_verb(arguments)
    options = verb_options(arguments)
    if options is None:
        print(USAGE, file=sys.stderr)
        return 2
    return scope_verb(options["--scope"], options.get("--feature"))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except NotUtf8 as error:
        print(f"check-decisions: {error}", file=sys.stderr)
        sys.exit(1)
    except OSError as error:
        print(f"check-decisions failed: {error}", file=sys.stderr)
        sys.exit(1)
