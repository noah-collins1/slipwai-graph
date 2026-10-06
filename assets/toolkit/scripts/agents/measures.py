"""What `benchmark.py` derives, at read time, from the records and from what git and the cruise log already say:
when a slice became ready and when it was accepted, how much of that interval it was worked, and how the rest was
spent waiting. Nothing here is written to a record (D65), and nothing here imports `benchmark.py`, which runs as
`__main__` and loads this file by path: whatever is needed — the project root, the records, a `git` callable that
returns a command's stripped stdout or None, the parsed cruise log — is passed in.

A figure is a number of seconds, or `{"unknown": "<reason>"}`; it is never a guess, and each names where it was
read from. Times are integer UTC seconds, printed as `YYYY-MM-DDTHH:MM:SSZ`.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GitFn = Callable[..., "str | None"]
Interval = tuple[int, int]
CAUSES = ("integration", "dependency", "review", "worker")  # the order in which they claim a second
GRAPH = "## Slice graph"


def utc(seconds: int) -> str:
    return datetime.fromtimestamp(seconds, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def epoch(text: str) -> int:
    return int(datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp())


def unknown(reason: str) -> dict[str, str]:
    return {"unknown": reason}


def is_unknown(figure: Any) -> bool:
    return isinstance(figure, dict) and "unknown" in figure


# --- intervals --------------------------------------------------------------------------------------------------

def union(intervals: list[Interval]) -> list[Interval]:
    merged: list[Interval] = []
    for start, end in sorted(interval for interval in intervals if interval[1] > interval[0]):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def length(intervals: list[Interval]) -> int:
    return sum(end - start for start, end in union(intervals))


def clip(intervals: list[Interval], low: int, high: int) -> list[Interval]:
    return union([(max(start, low), min(end, high)) for start, end in intervals])


def subtract(intervals: list[Interval], taken: list[Interval]) -> list[Interval]:
    """`intervals` less every second in `taken`."""
    left = union(intervals)
    for cut_start, cut_end in union(taken):
        pieces: list[Interval] = []
        for start, end in left:
            if cut_end <= start or cut_start >= end:
                pieces.append((start, end))
                continue
            if start < cut_start:
                pieces.append((start, cut_start))
            if cut_end < end:
                pieces.append((cut_end, end))
        left = pieces
    return left


# --- git moments ------------------------------------------------------------------------------------------------

Found = tuple[int, str, str]  # (committer time, short sha, where it was read)


def graph_rows(text: str) -> list[tuple[str, list[str]]]:
    """The `## Slice graph` table of a `story-split.md`: each row's slice and its `depends_on` ids, in row order."""
    rows: list[tuple[str, list[str]]] = []
    inside = False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line.strip() == GRAPH
            continue
        if inside and line.strip().startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            first = cells[0].strip("`")
            if len(cells) > 1 and first and not set(first) <= set("-: ") and first.lower() != "slice":
                rows.append((first, re.findall(r"`([^`]+)`", cells[1])))
    return rows


def model_blocks(text: str) -> dict[str, str]:
    """`docs/event-model/model.yaml`'s slice blocks by id (each runs from `- id:` to the next)."""
    blocks: dict[str, str] = {}
    for block in re.split(r"^\s*- id:\s*", text, flags=re.M)[1:]:
        blocks[block.split("\n", 1)[0].strip().strip("'\"")] = block
    return blocks


def block_dependencies(block: str) -> list[str]:
    inline = re.search(r"^\s*depends_on:\s*\[([^\]]*)\]", block, re.M)
    if inline:
        return [part.strip().strip("'\"") for part in inline.group(1).split(",") if part.strip()]
    listed = re.search(r"^(\s*)depends_on:\s*\n((?:\1\s+-\s*.+\n?)*)", block, re.M)
    return [item.strip().strip("'\"") for item in re.findall(r"-\s*(.+)", listed.group(2))] if listed else []


def register_has(text: str, ident: str) -> bool:
    return any(line.strip().startswith("|") and line.strip().strip("|").split("|")[0].strip().strip("`") == ident
               for line in text.splitlines())


class Reader:
    """The moments one feature's slices have in git, found once and kept."""

    def __init__(self, root: Path, feature: str, git: GitFn) -> None:
        self.root, self.feature, self.git = root, feature, git
        self.split = f"specs/{feature}/story-split.md"
        self.register = f"specs/{feature}/slices/README.md"
        self.model = "docs/event-model/model.yaml"
        self.kept: dict[tuple[str, str], Found | None] = {}
        self.seen: bool | None = None

    @property
    def readable(self) -> bool:
        if self.seen is None:
            self.seen = self.git("rev-parse", "--git-dir") is not None
        return self.seen

    def first(self, path: str, needle: str, holds: Callable[[str], bool]) -> tuple[int, str] | None:
        """The oldest commit that changed how often `needle` appears in `path` and whose copy of the file satisfies
        `holds` — the content check keeps `S1` from matching `S10`."""
        listed = self.git("log", "--reverse", "--format=%H %ct", f"-S{needle}", "--", path) or ""
        for line in listed.splitlines():
            sha, _, when = line.partition(" ")
            content = self.git("show", f"{sha}:{path}")
            if content is not None and holds(content):
                return int(when), sha[:7]
        return None

    def added(self, ident: str) -> Found | None:
        key = ("added", ident)
        if key not in self.kept:
            found = self.first(self.split, f"`{ident}`", lambda text: f"`{ident}`" in text)
            where = f"story-split.md: {ident}"
            if found is None:
                found = self.first(self.model, f"id: {ident}", lambda text: ident in model_blocks(text))
                where = f"model.yaml: {ident}"
            self.kept[key] = (found[0], found[1], where) if found else None
        return self.kept[key]

    def done(self, ident: str) -> Found | None:
        """The slice's done mark: a register row, or `status: implemented` in the model — the earlier of the two."""
        key = ("done", ident)
        if key not in self.kept:
            rows = self.first(self.register, f"`{ident}`", lambda text: register_has(text, ident))
            marked = self.first(self.model, "status: implemented",
                                lambda text: bool(re.search(r"^\s*status:\s*implemented\s*$",
                                                            model_blocks(text).get(ident, ""), re.M)))
            options = [(found[0], found[1], where) for found, where in
                       ((rows, f"slices/README.md: {ident}"), (marked, f"model.yaml: {ident} implemented")) if found]
            self.kept[key] = min(options) if options else None
        return self.kept[key]

    def merged(self, ident: str) -> Found | None:
        key = ("merged", ident)
        if key not in self.kept:
            listed = self.git("log", "--merges", "--reverse", "--fixed-strings", f"--grep=slice/{ident}",
                              "--format=%H %ct %s") or ""
            pattern = re.compile(r"slice/" + re.escape(ident) + r"(?![A-Za-z0-9])")
            self.kept[key] = next(((int(parts[1]), parts[0][:7], "merge commit") for parts in
                                   (line.split(" ", 2) for line in listed.splitlines())
                                   if len(parts) == 3 and pattern.search(parts[2])), None)
        return self.kept[key]

    def order(self) -> list[tuple[str, list[str]]]:
        path = self.root / self.split
        return graph_rows(path.read_text(encoding="utf-8")) if path.is_file() else []

    def dependencies(self, ident: str) -> list[str]:
        for slice_, deps in self.order():
            if slice_ == ident:
                return deps
        path = self.root / self.model
        block = model_blocks(path.read_text(encoding="utf-8")).get(ident) if path.is_file() else None
        return block_dependencies(block) if block else []


def moments(reader: Reader, ident: str | None, entries: list[dict[str, Any]]) -> dict[str, Any]:
    """`ready`, `accepted`, `elapsed` (each seconds or unknown), `demo_accepted` and `merged` where there are any,
    and `read_from` — where each was read. Elapsed is accepted minus ready."""
    read_from: dict[str, str] = {}
    out: dict[str, Any] = {"read_from": read_from}
    if not ident:
        out.update({key: unknown("a feature record is not a slice") for key in ("ready", "accepted", "elapsed")})
        return out
    if not reader.readable:
        out.update({key: unknown("git could not be read: not a repository, or git failed")
                    for key in ("ready", "accepted", "elapsed")})
        return out
    demo = next((entry for entry in entries if entry.get("stage") == "demo" and "ended" in entry
                 and (entry.get("signals") or {}).get("outcome") == "accepted"), None)
    if demo is not None:
        try:
            out["demo_accepted"] = epoch(demo["ended"])
            read_from["demo_accepted"] = f"the demo bracket ended {demo['ended']}"
        except ValueError:
            pass
    merged = reader.merged(ident)
    if merged:
        out["merged"], read_from["merged"] = merged[0], f"{merged[1]} ({merged[2]}: slice/{ident})"
    added = reader.added(ident)
    ready: Any
    if added is None:
        ready = unknown(f"{ident} is in neither {reader.split} nor {reader.model}")
    else:
        ready, read_from["ready"] = added[0], f"{added[1]} ({added[2]})"
        for dep in reader.dependencies(ident):
            landed = reader.done(dep)
            if landed is None:
                ready = unknown(f"not ready: {dep} is not done")
                read_from.pop("ready", None)
                break
            if landed[0] > ready:
                ready, read_from["ready"] = landed[0], f"{landed[1]} ({landed[2]})"
    own = reader.done(ident)
    out["ready"] = ready
    if own:
        out["accepted"], read_from["accepted"] = own[0], f"{own[1]} ({own[2]})"
    else:
        out["accepted"] = unknown(f"open since {utc(ready)}") if isinstance(ready, int) else ready
    if is_unknown(ready):
        out["elapsed"] = ready
    elif is_unknown(out["accepted"]):
        out["elapsed"] = out["accepted"]
    elif out["accepted"] < ready:
        out["elapsed"] = unknown(f"accepted ({utc(out['accepted'])}) precedes ready ({utc(ready)})")
    else:
        out["elapsed"] = out["accepted"] - ready
    return out


def printed(figure: Any) -> Any:
    """A moment for `--json` and the page: its UTC text, or the unknown as it is."""
    return figure if is_unknown(figure) or figure is None else utc(figure)


def parse_log(text: str) -> list[dict[str, Any]]:
    """The cruise log's rows (a line that is not JSON is skipped)."""
    rows = []
    for line in text.splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


# --- worked time and waiting ------------------------------------------------------------------------------------

FOREVER = 1 << 62
LOG = "specs/cruise-log.jsonl"


def bounds(entry: dict[str, Any], last_line: int | None = None) -> Interval | None:
    """An ended entry's bracket: from `started` to `ended`, or to the last transcript line attributed to it where
    one is given (a cut-off entry's `ended` is when the cut-off ran, not when the work did)."""
    try:
        start, end = epoch(entry["started"]), epoch(entry["ended"])
    except (KeyError, ValueError, TypeError):
        return None
    if last_line is not None and entry.get("cut_off"):
        end = min(end, max(start, last_line))
    return (start, end)


def is_person_demo(entry: dict[str, Any]) -> bool:
    """A `demo` bracket whose signals name no `driver`: a person at the demo, which is review's wait, not work."""
    return entry.get("stage") == "demo" and not (entry.get("signals") or {}).get("driver")


def brackets(entries: list[dict[str, Any]], last_lines: dict[int, int] | None = None,
             keep: Callable[[dict[str, Any]], bool] = lambda entry: True) -> list[Interval]:
    found = []
    for index, entry in enumerate(entries):
        if "ended" in entry and keep(entry):
            span = bounds(entry, (last_lines or {}).get(index))
            if span:
                found.append(span)
    return found


def worked(entries: list[dict[str, Any]], last_lines: dict[int, int] | None = None) -> list[Interval]:
    """The union of the record's brackets, less the `gate` (integration's) and a person's `demo` (review's), so a
    skipper nested inside an implement counts once."""
    return union(brackets(entries, last_lines,
                          lambda entry: entry.get("stage") != "gate" and not is_person_demo(entry)))


def stage_seconds(entries: list[dict[str, Any]], last_lines: dict[int, int] | None = None) -> int:
    """Stage time: what the entries add up to, each counted whole, so a skipper inside an implement is added to it
    (worked time counts that interval once). `last_lines` maps an entry's index to the moment of the last
    transcript line attributed to it, which ends a cut-off entry there; where none is given the recorded end stands."""
    total = 0
    for index, entry in enumerate(entries):
        if "ended" not in entry:
            continue
        span = bounds(entry, (last_lines or {}).get(index))
        total += span[1] - span[0] if span else int(entry.get("seconds", 0))
    return total


def cut_off_notes(label: str, entries: list[dict[str, Any]], last_lines: dict[int, int] | None = None) -> list[str]:
    """For each cut-off entry, where its stage time ends and why: its last attributed transcript line, or its
    recorded end because no transcript line could be read."""
    notes = []
    for index, entry in enumerate(entries):
        if not entry.get("cut_off") or "ended" not in entry:
            continue
        last = (last_lines or {}).get(index)
        if last is None:
            notes.append(f"{label} {entry['stage']}: stage time ends at its recorded end {entry['ended']} — its "
                         "transcript's last line could not be read")
        else:
            notes.append(f"{label} {entry['stage']}: stage time ends at its last transcript line {utc(last)}, not at "
                         f"the recorded end {entry['ended']}")
    return notes


def iterations(rows: list[dict[str, Any]]) -> list[Interval]:
    spans = []
    for row in rows:
        try:
            spans.append((epoch(row["started"]), epoch(row["ended"])))
        except (KeyError, ValueError, TypeError):
            continue
    return spans


def parks(rows: list[dict[str, Any]]) -> list[Interval]:
    """Each iteration ending `stopped: human`, up to the next iteration's start (open-ended where none follows)."""
    found = []
    for index, row in enumerate(rows):
        if str(row.get("last_line", "")).rstrip().endswith("stopped: human"):
            try:
                begun = epoch(row["ended"])
                later = epoch(rows[index + 1]["started"]) if index + 1 < len(rows) else FOREVER
            except (KeyError, ValueError, TypeError):
                continue
            found.append((begun, later))
    return found


def landing(reader: Reader, ident: str) -> Found | None:
    """When a sibling reached the branch: its merge commit, else its done mark."""
    return reader.merged(ident) or reader.done(ident)


def sibling_wait(reader: Reader, ident: str, demo: int, before: int) -> tuple[Interval, str] | None:
    """The wait a slice had after its demo was accepted: until the latest sibling earlier in split order landed,
    where that landing falls before `before` (the slice's own merge, or its acceptance)."""
    best: Found | None = None
    for sibling, _ in reader.order():
        if sibling == ident:
            break
        found = landing(reader, sibling)
        if found and demo < found[0] < before and (best is None or found[0] > best[0]):
            best = (found[0], found[1], f"{found[2]} of {sibling}")
    return ((demo, best[0]), f"{best[1]} ({best[2]})") if best else None


def waiting(found: dict[str, Any], reader: Reader, ident: str, entries: list[dict[str, Any]],
            log: list[dict[str, Any]], last_lines: dict[int, int] | None = None) -> dict[str, Any]:
    """worked, and each cause's seconds, inside [ready, accepted]: every second goes to the first claimant in the
    order worked, integration, dependency, review, worker, and what no record claims is unattributed, so the parts
    add up to elapsed exactly. Unknown wherever elapsed is."""
    names = (*CAUSES, "unattributed")
    read_from: dict[str, str] = {}
    if is_unknown(found["elapsed"]):
        reason = found["elapsed"]
        return {"worked": reason, "waiting": {name: reason for name in names}, "read_from": read_from}
    low, high = found["ready"], found["accepted"]
    taken = clip(worked(entries, last_lines), low, high)
    read_from["worked_seconds"] = "the record's brackets"
    claimed: dict[str, list[Interval]] = {}
    gates = brackets(entries, last_lines, lambda entry: entry.get("stage") == "gate")
    integration = list(gates)
    if "merged" in found:
        integration.append((found["merged"], high))
    read_from["integration"] = ", ".join(
        part for part in ((found["read_from"]["merged"] if "merged" in found else ""),
                          f"{len(gates)} gate bracket(s)" if gates else "") if part) or "none present: no merge commit, no gate bracket"
    claimed["integration"] = integration
    claimed["dependency"] = []
    read_from["dependency"] = "none present: no accepted demo, or no sibling landed after it"
    if "demo_accepted" in found:
        waited = sibling_wait(reader, ident, found["demo_accepted"], found.get("merged", high))
        if waited:
            claimed["dependency"], read_from["dependency"] = [waited[0]], waited[1]
    review = brackets(entries, last_lines, is_person_demo)
    claimed["review"] = review
    read_from["review"] = "the demo bracket with no driver" if review else "none present: no park, no person's demo"
    claimed["worker"] = []
    read_from["worker"] = "none present: no cruise log"
    if log:
        parked = parks(log)
        span = iterations(log)
        claimed["review"] = review + parked
        read_from["review"] = f"{LOG}: stopped: human" if parked else read_from["review"]
        if span:
            claimed["worker"] = [(min(start for start, _ in span), max(end for _, end in span))]
            read_from["worker"] = f"{LOG}: the log's span, less parks"
    seconds: dict[str, int] = {}
    for cause in CAUSES:
        mine = subtract(clip(claimed[cause], low, high), taken)
        seconds[cause] = length(mine)
        taken = union(taken + mine)
    in_worked = length(clip(worked(entries, last_lines), low, high))
    seconds["unattributed"] = (high - low) - length(taken)
    return {"worked": in_worked, "waiting": seconds, "read_from": read_from}
