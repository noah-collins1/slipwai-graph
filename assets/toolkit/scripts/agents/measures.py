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


SLICE_ID = re.compile(r"[A-Za-z]+\d+(?![A-Za-z0-9_])(?:[.-][A-Za-z0-9._-]*[A-Za-z0-9])?")  # the head, then a slug


def cell_ids(cell: str) -> list[str]:
    """The slice ids a table cell names, in order: backticked as they are, bare where they have an id's shape;
    `—`, `-`, an empty cell and prose name none."""
    return [ticked or bare for ticked, bare in re.findall(r"`([^`]+)`|([^\s,;`]+)", cell)
            if ticked or SLICE_ID.fullmatch(bare)]


def first_id(cell: str) -> str:
    """The slice a row's first cell names, backticked or bare (the rule `benchmark.py`'s `done_slices` applies)."""
    ticked = re.match(r"\s*`([^`]+)`", cell)
    found = SLICE_ID.match(cell.strip())
    return ticked.group(1) if ticked else found.group(0) if found else ""


def mentions(text: str, ident: str) -> bool:
    """Whether `ident` appears in `text` as a whole id — `S1` is not in `S10` or `S1-a`."""
    return re.search(r"(?<![A-Za-z0-9_.-])" + re.escape(ident) + r"(?![A-Za-z0-9_]|[.-][A-Za-z0-9])", text) is not None


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
            first = first_id(cells[0])
            if len(cells) > 1 and first and first.lower() != "slice":
                rows.append((first, cell_ids(cells[1])))
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
    return any(line.strip().startswith("|") and first_id(line.strip().strip("|").split("|")[0]) == ident
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
        self.shallow_seen: bool | None = None
        self.failure: str | None = None  # the first `git` command a lookup depended on that failed

    @property
    def shallow(self) -> bool:
        """Whether the history is truncated (`--depth`): the oldest commit holding a row is then the graft, not the
        commit that wrote it, so every moment it gives is wrong."""
        if self.shallow_seen is None:
            self.shallow_seen = self.git("rev-parse", "--is-shallow-repository") == "true"
        return self.shallow_seen

    def ask(self, *arguments: str) -> str | None:
        """`git`'s answer: an empty string is an answer (nothing found), None is a failure, kept in `failure`."""
        found = self.git(*arguments)
        if found is None and self.failure is None:
            self.failure = f"git failed: git {' '.join(arguments)}"
        return found

    @property
    def readable(self) -> bool:
        if self.seen is None:
            self.seen = self.git("rev-parse", "--git-dir") is not None
        return self.seen

    def first(self, path: str, needle: str, holds: Callable[[str], bool]) -> tuple[int, str] | None:
        """The oldest commit that changed how often `needle` appears in `path` and whose copy of the file satisfies
        `holds` — the content check keeps `S1` from matching `S10`."""
        listed = self.ask("log", "--reverse", "--format=%H %ct", f"-S{needle}", "--", path) or ""
        for line in listed.splitlines():
            sha, _, when = line.partition(" ")
            content = self.git("show", f"{sha}:{path}")
            if content is None and self.ask("ls-tree", "--name-only", sha, "--", path):
                self.failure = self.failure or f"git failed: git show {sha[:7]}:{path}"  # it is there and unreadable
            if content is not None and holds(content):
                return int(when), sha[:7]
        return None

    def added(self, ident: str) -> Found | None:
        key = ("added", ident)
        if key not in self.kept:
            found = self.first(self.split, ident, lambda text: mentions(text, ident))
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
            rows = self.first(self.register, ident, lambda text: register_has(text, ident))
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
            listed = self.ask("log", "--merges", "--reverse", "--fixed-strings", f"--grep=slice/{ident}",
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
    if reader.shallow:
        out.update({key: unknown("git history is shallow: the oldest commit is where the clone was cut, not where a "
                                 "row was written; fetch the full history") for key in ("ready", "accepted", "elapsed")})
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
    if reader.failure:
        out.update({key: unknown(reader.failure) for key in ("ready", "accepted", "elapsed")})
        for key in ("ready", "accepted", "merged"):
            read_from.pop(key, None)
        out.pop("merged", None)
        return out
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


def entry_seconds(entry: dict[str, Any], last_line: int | None = None) -> Any:
    """One entry's stage time; unknown, with the reason, for an entry still open or one never bracketed — it has no
    stage time to read, and `0` would say it had one."""
    if "ended" not in entry:
        return unknown("the entry is still open")
    if entry.get("seconds") == 0:
        return unknown("not recorded: the stage was not bracketed around its work")
    return stage_seconds([entry], {0: last_line} if last_line is not None else None)


REFUSED = ("behaviour", "implementation")
TOKEN_KEYS = ("input", "output", "cache_read", "cache_creation")


def recorded_tokens(entry: dict[str, Any]) -> Any:
    """What the entry's own `usage` says it cost — the four counts over every model, host and delegates — or why
    nothing was read. An unbracketed entry has no tokens to read (its start and end were the same moment)."""
    usage = entry.get("usage") or {}
    if "ended" not in entry:
        return unknown("the entry is still open")
    if entry.get("seconds") == 0:
        return unknown("not recorded: the stage was not bracketed around its work")
    if not usage.get("source"):
        return unknown(f"not recorded: {usage.get('reason') or 'no usage was read'}")
    return sum(tokens.get(key, 0) for part in ("host", "subagents") for tokens in (usage.get(part) or {}).values()
               for key in TOKEN_KEYS)


def sum_figures(figures: list[Any]) -> Any:
    """The sum of figures, or the first reason one of them is unknown: a total is never made of a guess."""
    for figure in figures:
        if is_unknown(figure):
            return figure
    return sum(figures)


def rework_indices(entries: list[dict[str, Any]]) -> list[int]:
    """Every entry after a `demo` whose outcome was `behaviour` or `implementation`, up to (not including) the next
    `demo`, or to the record's end: what a demo that was not accepted sent back. After an `accepted` one, none."""
    found = []
    refused = False
    for index, entry in enumerate(entries):
        if entry.get("stage") == "demo":
            refused = (entry.get("signals") or {}).get("outcome") in REFUSED
        elif refused and "ended" in entry:
            found.append(index)
    return found


def rework(entries: list[dict[str, Any]], tokens: list[Any], last_lines: dict[int, int] | None = None) -> dict[str, Any]:
    """The rework entries' stage time and tokens (`tokens[i]` is entry `i`'s figure)."""
    chosen = rework_indices(entries)
    kept = {new: (last_lines or {})[old] for new, old in enumerate(chosen) if old in (last_lines or {})}
    return {"seconds": stage_seconds([entries[index] for index in chosen], kept),
            "tokens": sum_figures([tokens[index] for index in chosen])}


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
    if reader.failure:  # a lookup the dependency wait made failed: nothing it would have claimed can be said
        reason = unknown(reader.failure)
        return {"worked": reason, "waiting": {name: reason for name in names}, "read_from": read_from}
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


TRANSCRIPTS = "the transcripts, by delegate and bracket"
RECORDED = "the entries' recorded usage"


def cost_source(read: dict[str, int] | None, ended: int) -> str:
    """Where a record's cost was read from, by the entries each source supplied: both, with counts, where it is
    mixed; `none present` where no ended entry's cost could be read."""
    read = read or {}
    transcripts, recorded, unread = (read.get(key, 0) for key in ("transcripts", "recorded", "unread"))
    entries = lambda count: f"{count} entr{'y' if count == 1 else 'ies'}"  # noqa: E731
    if transcripts and recorded:
        said = f"{TRANSCRIPTS} ({entries(transcripts)}) and {RECORDED} ({entries(recorded)})"
    elif transcripts or recorded:
        said = TRANSCRIPTS if transcripts else RECORDED
    else:
        return "none present: no bracket ended" if not ended else "none present: no ended entry's cost could be read"
    return said + (f"; {entries(unread)} unread" if unread else "")


def entry_source(source: str | None, tokens: Any) -> str:
    """Where one entry's tokens were read from: its transcripts, its recorded usage, or what was found absent."""
    if is_unknown(tokens):
        return f"none present: {tokens['unknown']}"
    return TRANSCRIPTS if source == "transcripts" else RECORDED


def sources(moved: dict[str, Any], parts: dict[str, Any], ended: int, reworked: int,
            cost_read: dict[str, int] | None) -> dict[str, str]:
    """`read_from` for every figure `--json` carries — a figure no record supports says what was looked at and found
    absent (`none present: …`), so a `0` is never the only word about it. `moved` and `parts` are `moments` and
    `waiting`'s results; `reworked` counts the entries a refused demo sent back; `cost_read` is how many entries'
    costs attribution read from the transcripts and from recorded usage."""
    found = {**moved["read_from"], **parts["read_from"]}
    if is_unknown(moved["elapsed"]):
        found["elapsed"] = f"none present: {moved['elapsed']['unknown']}"
        for key in ("worked_seconds", "dependency", "worker", "review", "integration", "unattributed"):
            found[key] = found["elapsed"]
    else:
        found["elapsed"] = f"ready: commit {found.get('ready', '')}; accepted: commit {found.get('accepted', '')}"
        found["unattributed"] = "elapsed less worked time and every cause above: what no bracket, commit or log claims"
    found["stage_seconds"] = f"the record's brackets ({ended} ended)" if ended else "none present: no bracket ended"
    found["rework"] = (f"the {reworked} entr{'y' if reworked == 1 else 'ies'} after a refused demo's bracket" if reworked
                       else "none present: no demo was refused")
    found["cost"] = cost_source(cost_read, ended)
    return found


# --- the feature's figures --------------------------------------------------------------------------------------

def feature_figures(parts: list[dict[str, Any]]) -> dict[str, Any]:
    """One feature's three figures from its records, each a dict with `slice` (None for the feature's own record),
    `ready`, `accepted` (seconds or unknown), `stage_seconds` and `worked` (the bracket intervals, unclipped):
    `elapsed` is the first slice's ready to the last slice's accepted — unknown while any slice's ready moment is
    unread, open while any slice is not accepted —
    `stage_seconds` every record's stage time summed (the feature's own included), and `in_flight_seconds` the length
    of the union of every slice record's worked brackets: the time with any slice in flight."""
    slices = [part for part in parts if part["slice"]]
    readies = [part["ready"] for part in slices if isinstance(part["ready"], int)]
    unread = next((part for part in slices if is_unknown(part["ready"])), None)
    elapsed: Any
    if not slices:
        elapsed = unknown("no slice record")
    elif unread is not None:  # a figure is printed only when every slice's ready and accepted moments were read
        elapsed = unknown(f"{unread['slice']}: {unread['ready']['unknown']}")
    elif any(not isinstance(part["accepted"], int) for part in slices):
        elapsed = unknown(f"open since {utc(min(readies))}")
    else:
        elapsed = max(part["accepted"] for part in slices) - min(readies)
    return {"elapsed": elapsed, "stage_seconds": sum(part["stage_seconds"] for part in parts),
            "in_flight_seconds": length([span for part in slices for span in part["worked"]])}


# --- decision health --------------------------------------------------------------------------------------------

# How a decision entry spells what decision health reads. This is the plan's Q1 option (a), pending the host's number
# (S26 writes the `Reversibility:` line, S28 the review statuses): when either changes a spelling, it changes here.
SPELLING = {
    "entry": re.compile(r"^## D\d+ — ", re.M),      # an entry opens on this line
    "tier_line": re.compile(r"^- \*\*Reversibility:\*\*(.*)$", re.M),
    "tiers": ("easy", "guarded", "hard"),           # the first of these on the line is the entry's tier
    "escalation": re.compile(r"\b(?:easy|guarded)\s*(?:→|->)\s*hard\b"),
    "status_line": re.compile(r"^- \*\*Status:\*\*(.*)$", re.M),
    "reviewed": ("ratified", "reverted"),           # a review's verdict, as the Status line says it
    "reverted": "reverted",
    "when": re.compile(r"\*\*When:\*\*\s*(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)"),
}
NO_TIER = "no decision entry carries a Reversibility: line"
BAND = (5, 15)      # escalation share, percent, inclusive: outside it is flagged
OVER = 5            # misclassification rate, percent: over it is flagged


def decision_entries(text: str) -> list[dict[str, Any]]:
    """Each entry's tier (None where it has none), whether it escalated, its status and the moment it was written."""
    found = []
    for part in SPELLING["entry"].split(text)[1:]:
        line = SPELLING["tier_line"].search(part)
        status = SPELLING["status_line"].search(part)
        when = SPELLING["when"].search(part)
        value = line.group(1) if line else ""
        words = re.findall(r"\b(" + "|".join(SPELLING["tiers"]) + r")\b", value)
        found.append({"tier": words[0] if words else None, "escalated": bool(SPELLING["escalation"].search(value)),
                      "status": status.group(1) if status else "", "when": epoch(when.group(1)) if when else None})
    return found


def share(numerator: int, denominator: int, none: str, flagged: Callable[[int, int], bool], why: str) -> dict[str, Any]:
    """A rate in percent (a whole number where it is whole, else one decimal), or unknown naming the empty denominator."""
    if denominator == 0:
        return unknown(none)
    exact = numerator * 100 / denominator
    return {"percent": int(exact) if numerator * 100 % denominator == 0 else round(exact, 1),
            "numerator": numerator, "denominator": denominator,
            "flagged": flagged(numerator, denominator), "why": why if flagged(numerator, denominator) else None}


def median(values: list[int]) -> int | float:
    ordered = sorted(values)
    middle = len(ordered) // 2
    return ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2


def decision_health(text: str, skippers: list[tuple[int, int, int]]) -> dict[str, Any]:
    """The feature's escalation share, misclassification rate and median wait by tier, from its `decisions.md` and
    the `skipper` brackets of its records, each `(start, end, seconds)`. A figure nothing supports is unknown, with why."""
    entries = decision_entries(text)
    tiered = [entry for entry in entries if entry["tier"]]
    if not tiered:
        return {key: unknown(NO_TIER) for key in ("escalation_share", "misclassification_rate", "median_wait")}
    scored = [entry for entry in tiered if entry["tier"] != "hard"]
    reviewed = [entry for entry in tiered if any(word in entry["status"] for word in SPELLING["reviewed"])]
    waits: dict[str, Any] = {}
    for tier in SPELLING["tiers"]:
        mine = [entry for entry in tiered if entry["tier"] == tier]
        # The shortest bracket holding the moment is the skipper that decided it, not an enclosing one.
        reads = [min(held, key=lambda span: span[1] - span[0])[2] for entry in mine if entry["when"] is not None
                 if (held := [span for span in skippers if span[0] <= entry["when"] <= span[1]])]
        waits[tier] = median(reads) if reads else unknown(
            f"no {tier} entry" if not mine else f"no skipper bracket holds the When: moment of any {tier} entry")
    return {
        "escalation_share": share(sum(entry["escalated"] for entry in scored), len(scored),
                                  "no entry is scored easy or guarded",
                                  lambda top, bottom: not BAND[0] * bottom <= top * 100 <= BAND[1] * bottom,
                                  f"outside the healthy band {BAND[0]}–{BAND[1]}%"),
        "misclassification_rate": share(sum(SPELLING["reverted"] in entry["status"] for entry in reviewed),
                                        len(reviewed), "no tiered entry was ratified or reverted",
                                        lambda top, bottom: top * 100 > OVER * bottom, f"over {OVER}%"),
        "median_wait": waits,
    }


def percent_text(percent: int | float) -> str:
    return f"{percent}%"


def health_lines(health: dict[str, Any], wall: Callable[[int], str]) -> list[str]:
    """The three lines the aggregate and the page print: a figure with its numerator and denominator and, where it is
    flagged, why; or `unknown — <reason>` with no number."""
    def rate(figure: Any, name: str, of: str) -> str:
        if is_unknown(figure):
            return f"{name}: unknown — {figure['unknown']}"
        return (f"{name}: {percent_text(figure['percent'])} ({figure['numerator']} of {figure['denominator']} {of})"
                + (f" — {figure['why']}" if figure["flagged"] else ""))
    waits = health["median_wait"]
    if is_unknown(waits):
        wait = f"median wait: unknown — {waits['unknown']}"
    else:
        wait = "median wait: " + ", ".join(
            f"{tier} unknown ({figure['unknown']})" if is_unknown(figure) else f"{tier} {wall(round(figure))}"
            for tier, figure in waits.items())
    return [rate(health["escalation_share"], "escalation share", "entries scored easy or guarded"),
            rate(health["misclassification_rate"], "misclassification rate", "reviewed"), wait]
