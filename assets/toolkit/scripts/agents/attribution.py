"""Which record, and which entry of it, each request of each session belongs to — so that a request is counted in
exactly one place and a bracket open at the same time as another does not take what is not its own.

`benchmark.py` runs as `__main__` and loads this file by path (bytecode off), once per process; this file never
imports it, so everything it needs is passed to `attribute()`: the records, the project root, a function that finds a
session's transcripts, one that makes an entry's window, the table of which stage owns which delegate type, and one
that reads an entry's recorded usage. The reading is of what a transcript already says, never asked:

1. a *request* is the first assistant line of its `requestId` (else `message.id`, else `uuid`) that carries
   `message.usage`, the main transcript first, then the sub-agent files in name order;
2. a sub-agent's *chain* is its `agent-<a>.meta.json` and then its `parentAgentId`'s, upwards, to the first
   `agentType == "drive-slice"`, whose description names the slice;
3. a window's *opener* is the file whose bytes at the window's cursor print `benchmark: <stage> started (<record>`;
   its chain is the window's class (none: the host's);
4. a request with a chain goes to the slice's record; one without goes to a host-opened bracket covering it, and to
   the shared bucket where none does or where brackets of several records do with no stage owning its delegate type.

Nothing is written; the figures are derived again each time. A figure is a number of tokens, or
`{"unknown": "<reason>"}`.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OPENER_BYTES = 1 << 20
FIELDS = ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
PARTS = ("total", "attributed", "shared")
UNRESOLVED = "<unresolved>"
Figure = Any  # an int, or {"unknown": reason}


def unknown(reason: str) -> dict[str, str]:
    return {"unknown": reason}


def stamp(text: Any) -> str | None:
    """A transcript's `2026-10-05T17:17:50.123Z` as `2026-10-05T17:17:50Z`; none where it is not one."""
    if isinstance(text, str) and len(text) >= 19:
        try:
            datetime.strptime(text[:19], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return None
        return text[:19] + "Z"
    return None


def epoch(text: str) -> int:
    return int(datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp())


class Request:
    """One API response. `when` is its first line's moment (where it began); `last` is the latest moment any of its
    lines carries (where it ended) — a response is written as a line per content block, seconds apart."""

    __slots__ = ("key", "file", "offset", "when", "agent", "tokens", "last")

    def __init__(self, key: str, file: str, offset: int, when: str | None, agent: str | None, tokens: int) -> None:
        self.key, self.file, self.offset, self.when, self.agent, self.tokens = key, file, offset, when, agent, tokens
        self.last = when


def read_requests(files: list[Path]) -> dict[str, Request]:
    """Every request in `files`, once: only the lines that carry `"usage"` are parsed, and a repeated key (one API
    response is written as a line per content block) keeps its first line, and the latest moment of any."""
    found: dict[str, Request] = {}
    for path in files:
        with path.open("rb") as handle:
            position = 0
            for raw in handle:
                start, position = position, position + len(raw)
                if b'"usage"' not in raw:
                    continue
                try:
                    item = json.loads(raw.decode("utf-8", errors="replace"))
                except ValueError:
                    continue
                message = item.get("message") if isinstance(item, dict) else None
                usage = message.get("usage") if isinstance(message, dict) else None
                if item.get("type") != "assistant" or not isinstance(usage, dict):
                    continue
                key = item.get("requestId") or message.get("id") or item.get("uuid")
                if not key:
                    continue
                if str(key) in found:
                    again = found[str(key)]
                    moment = stamp(item.get("timestamp"))
                    if moment and (again.last is None or moment > again.last):
                        again.last = moment
                    continue
                agent = item.get("attributionAgent") if isinstance(item.get("attributionAgent"), str) else None
                tokens = sum(usage[field] for field in FIELDS if isinstance(usage.get(field), int))
                found[str(key)] = Request(str(key), str(path), start, stamp(item.get("timestamp")), agent, tokens)
    return found


class Session:
    """One Claude Code session's transcripts, read once: its requests, and the chain of each sub-agent file."""

    def __init__(self, name: str, main: Path | None, subagents: list[Path]) -> None:
        self.name = name
        self.files = [path for path in [main, *sorted(subagents)] if path is not None]
        self.present = bool(self.files)
        self.requests = read_requests(self.files) if self.present else {}
        self._meta: dict[str, dict[str, Any] | None] = {}
        self.main = str(main) if main is not None else None

    def meta(self, path: Path) -> dict[str, Any] | None:
        key = str(path)
        if key not in self._meta:
            found = None
            if path.is_file():
                try:
                    loaded = json.loads(path.read_text(encoding="utf-8"))
                    found = loaded if isinstance(loaded, dict) else None
                except ValueError:
                    found = None
            self._meta[key] = found
        return self._meta[key]

    def meta_of(self, file: str) -> dict[str, Any] | None:
        path = Path(file)
        return None if file == self.main else self.meta(path.with_name(path.stem + ".meta.json"))

    def description(self, file: str) -> str | None:
        """What a sub-agent file says it is, for the entry's `delegates`; none for the main transcript."""
        found = self.meta_of(file)
        if found is None:
            return None if file == self.main else Path(file).stem
        return str(found.get("description") or found.get("agentType") or Path(file).stem)

    def chain(self, file: str) -> str | None:
        """The description of the first `drive-slice` at or above this file; none where there is none."""
        path = Path(file)
        found = self.meta_of(file)
        seen: set[str] = set()
        while found is not None:
            if found.get("agentType") == "drive-slice":
                return str(found.get("description") or "")
            parent = found.get("parentAgentId")
            if not isinstance(parent, str) or not parent or parent in seen:
                return None
            seen.add(parent)
            found = self.meta(path.with_name(f"agent-{parent.removeprefix('agent-')}.meta.json"))
        return None

    def opener(self, window_from: dict[str, int], needle: bytes) -> str | None:
        """The file, among those the window's cursor names, whose bytes there print the bracket's `started (` line."""
        for file in self.files:
            if str(file) not in window_from:
                continue
            with file.open("rb") as handle:
                handle.seek(window_from[str(file)])
                if needle in handle.read(OPENER_BYTES):
                    return str(file)
        return None


class Held:
    """One entry's window with what is known of it: the record and index it is in, the session, its class."""

    def __init__(self, path: str, index: int, entry: dict[str, Any], window: Any, session: str | None) -> None:
        self.path, self.index, self.entry, self.window, self.session = path, index, entry, window, session
        self.cls: str | None = None
        self.duplicate = False
        self.label = ""


def session_of(entry: dict[str, Any], window: Any) -> str | None:
    """The Claude Code session an entry ran in: the one its usage or cursor names, else the one its window's files
    are under (`<slug>/<session>.jsonl`, or `<slug>/<session>/subagents/agent-<a>.jsonl`)."""
    for part in (entry.get("usage"), entry.get("cursor")):
        if isinstance(part, dict) and part.get("source") == "claude" and part.get("session"):
            return str(part["session"])
    if window is not None:
        for key in list(window.from_) + list(window.to or {}):
            path = Path(key)
            if ".claude/projects" in key:
                return path.parent.parent.name if path.parent.name == "subagents" else path.stem
    return None


def slice_word(description: str) -> str:
    """The name a `drive-slice` description gives: the text after `drive-slice `, else the first word."""
    text = description.strip()
    if text.startswith("drive-slice "):
        return text[len("drive-slice "):].strip()
    return text.split()[0] if text.split() else ""


def resolve(word: str, slices: dict[str, list[str]]) -> str | None:
    """A record's path for a name: its slice exactly (the first record, where a copy exists), else the only record
    whose slice starts with `<word>-`."""
    if word in slices:
        return slices[word][0]
    starting = [paths[0] for name, paths in slices.items() if name.startswith(f"{word}-")] if word else []
    return starting[0] if len(starting) == 1 else None


def pick(request: Request, candidates: list[Held]) -> Held:
    """Inside one record, the entry the request is counted in: the window that counts it, else the latest started."""
    for held in candidates:
        if held.window.counts(request.file, request.offset, request.agent,
                              [other.window for other in candidates if other is not held]):
            return held
    return max(candidates, key=lambda held: held.window.order)


class Totals:
    def __init__(self) -> None:
        self.tokens = 0
        self.delegates: set[str] = set()
        self.last: str | None = None

    def add(self, request: Request, delegate: str | None) -> None:
        self.tokens += request.tokens
        if delegate:
            self.delegates.add(delegate)
        if request.last and (self.last is None or request.last > self.last):
            self.last = request.last


def overlapping(path: str, entry: dict[str, Any], others: dict[str, list[dict[str, Any]]],
                labels: dict[str, str]) -> str | None:
    """The label of another record with an ended bracket overlapping this entry's in time, if there is one. A
    bracket that names another session cannot have entered this entry's recorded usage, so it is not one."""
    try:
        start, end = epoch(entry["started"]), epoch(entry["ended"])
    except (KeyError, ValueError, TypeError):
        return None
    mine = session_of(entry, None)
    for other, entries in others.items():
        if other == path:
            continue
        for item in entries:
            try:
                theirs = session_of(item, None)
                if epoch(item["started"]) < end and start < epoch(item["ended"]) and (
                        mine is None or theirs is None or mine == theirs):
                    return labels[other]
            except (KeyError, ValueError, TypeError):
                continue
    return None


def attribute(records: list[tuple[Path, dict[str, Any]]], root: Path,
              find: Callable[[str], tuple[Path | None, list[Path]]], make_window: Callable[[dict[str, Any]], Any],
              recorded: Callable[[dict[str, Any]], Figure],
              elsewhere: Callable[[], tuple[dict[str, list[dict[str, Any]]], dict[str, str], str | None]] | None = None,
              ) -> dict[str, Any]:
    """Every record's per-entry `tokens`, `delegates` and `last_line`, its `cost`, and per feature the sessions'
    `total`, `attributed` and `shared` (which add up) and the notes the reading owes. `elsewhere` is asked, once and only
    when a recorded figure is about to stand, for the ended brackets of the records on other branches — `(entries by
    key, label by key, why not)`, `why not` set where git could not say — which a bracket here may overlap."""
    keys = [str(path) for path, _ in records]
    by_key = {str(path): record for path, record in records}
    labels = {key: str(record.get("slice") or "(feature)") for key, record in by_key.items()}
    slices: dict[str, list[str]] = {}
    for key, record in by_key.items():
        if record.get("slice"):
            slices.setdefault(str(record["slice"]), []).append(key)
    sessions: dict[str, Session] = {}
    notes_gone: set[str] = set()
    held: list[Held] = []
    used: dict[str, set[str]] = {key: set() for key in keys}  # the sessions each record's entries ran in
    missing: dict[tuple[str, int], list[str]] = {}  # the transcript files an entry's span names that are gone
    for key, record in by_key.items():
        for index, entry in enumerate(record.get("stages", [])):
            window = make_window(entry)
            name = session_of(entry, window)
            if name is not None:
                used[key].add(name)
                if name not in sessions:
                    sessions[name] = Session(name, *find(name))
            if window is not None and name is not None and sessions[name].present:
                gone = sorted(file for file in {*window.from_, *(window.to or {})}
                              if ".claude/projects" in file and not Path(file).is_file())
                if gone:  # a part of the session is missing: what the entry holds cannot be told from what is left
                    missing[(key, index)] = [Path(file).name for file in gone]
                    notes_gone.update(missing[(key, index)])
                else:
                    held.append(Held(key, index, entry, window, name))
    seen_windows: set[Any] = set()
    for item in held:  # a record merged from two branches carries the same bracket twice: it is counted once
        identity = (by_key[item.path].get("slice"), item.entry["stage"], item.entry.get("started"),
                    tuple(sorted(item.window.from_.items())), tuple(sorted((item.window.to or {}).items())))
        item.duplicate = identity in seen_windows
        seen_windows.add(identity)
    notes: dict[str, set[str]] = {name: set() for name in sessions}
    for item in held:
        session = sessions[str(item.session)]
        needle = f"benchmark: {item.entry['stage']} started ({Path(item.path).relative_to(root).as_posix()}".encode()
        file = session.opener(item.window.from_, needle)
        description = session.chain(file) if file else None
        item.cls = None if description is None else (resolve(slice_word(description), slices) or UNRESOLVED)

    far: tuple[dict[str, list[dict[str, Any]]], dict[str, str], str | None] | None = None
    abroad: list[Held] | None = None

    def elsewhere_once() -> tuple[dict[str, list[dict[str, Any]]], dict[str, str], str | None]:
        nonlocal far
        if far is None:
            far = elsewhere() if elsewhere is not None else ({}, {}, None)
        return far

    def foreign() -> list[Held]:
        """The brackets kept on other branches, as windows over the sessions read here, each with its class."""
        nonlocal abroad
        if abroad is None:
            abroad = []
            for fkey, items in elsewhere_once()[0].items():
                label = elsewhere_once()[1].get(fkey, fkey)
                for index, item in enumerate(items):
                    window = make_window(item)
                    who = session_of(item, window)
                    if window is None or who not in sessions or not sessions[who].present:
                        continue
                    needle = f"benchmark: {item['stage']} started ({fkey.split(':', 1)[1]}".encode()
                    file = sessions[who].opener(window.from_, needle)
                    other = Held(fkey, index, item, window, who)
                    other.cls = None if not file or sessions[who].chain(file) is None else UNRESOLVED
                    other.label = label
                    abroad.append(other)
        return abroad

    entries: dict[tuple[str, int], Totals] = {}
    loose: dict[str, int] = {key: 0 for key in keys}  # a slice's requests that no bracket of it covers
    spent: dict[str, dict[str, int]] = {key: {} for key in keys}  # attributed tokens, by record and session
    summary: dict[str, dict[str, Any]] = {}
    shared_requests: dict[str, list[Request]] = {}
    for name, session in sessions.items():
        mine = [item for item in held if item.session == name and not item.duplicate]
        attributed = shared_total = 0
        shared_requests[name] = []
        for request in session.requests.values():
            covering = [item for item in mine if item.window.covers(request.file, request.offset)]
            target: str | None = None
            chosen: Held | None = None
            description = session.chain(request.file)
            if description is not None:
                target = resolve(slice_word(description), slices)
                if target is None:
                    notes[name].add(f'drive-slice "{description}" names no recorded slice — its requests are in the '
                                    "shared bucket")
                else:
                    inside = [item for item in covering if item.path == target]
                    chosen = pick(request, [item for item in inside if item.cls == target] or inside) if inside else None
            else:
                host = [item for item in covering if item.cls is None]
                if host and elsewhere is not None:
                    host += [item for item in foreign() if item.session == name and item.cls is None
                             and item.window.covers(request.file, request.offset)]
                    if elsewhere_once()[2] is not None:
                        notes[name].add(f"{elsewhere_once()[2]}, so a request here may be a bracket of another "
                                        "slice's")
                targets = {item.path for item in host}
                if len(targets) > 1:
                    targets = {item.path for item in host if item.window.owns(request.agent)}
                    away = [item for item in host if item.path in targets and item.path not in by_key]
                    if away:
                        notes[name].add(f"requests of a bracket kept on {away[0].label} are in the shared bucket")
                if len(targets) == 1 and not any(item.window.owns(request.agent) for item in host) \
                        and covering and covering[0].window.owned(request.agent):
                    targets = set()  # a delegate type some stage runs, in a bracket of a stage that does not
                    notes[name].add(f"a {request.agent} delegate ran in no bracket of a stage that runs it — its "
                                    "requests are in the shared bucket")
                if len(targets) == 1 and next(iter(targets)) in by_key:
                    target = next(iter(targets))
                    chosen = pick(request, [item for item in host if item.path == target])
            if target is None:
                shared_total += request.tokens
                shared_requests[name].append(request)
                continue
            attributed += request.tokens
            spent[target][name] = spent[target].get(name, 0) + request.tokens
            if chosen is None:
                loose[target] += request.tokens
            else:
                entries.setdefault((target, chosen.index), Totals()).add(request, session.description(request.file))
        # the total is what the transcripts hold, summed on its own: a request the loop above dropped would show
        # as a total larger than the two parts
        summary[name] = {"total": sum(request.tokens for request in session.requests.values()),
                         "attributed": attributed, "shared": shared_total}

    others = {key: [item for item in by_key[key].get("stages", []) if "ended" in item] for key in keys}
    result: dict[str, Any] = {"records": {}, "features": {}}
    absent = lambda names: any(not sessions[name].present for name in names)  # noqa: E731
    for key, record in by_key.items():
        shown: dict[int, dict[str, Any]] = {}
        figures: list[Figure] = []
        read = {"transcripts": 0, "recorded": 0, "unread": 0, "open": 0}  # the entries the record's cost is made of, by source
        for index, entry in enumerate(record.get("stages", [])):
            done = entry.get("ended") is not None
            source = "transcripts"
            if (key, index) in entries or any(item.path == key and item.index == index for item in held):
                found = entries.get((key, index), Totals())
                shown[index] = {"tokens": found.tokens, "delegates": sorted(found.delegates), "last_line": found.last,
                                "searched": True}
            else:
                source = "recorded"
                figure = recorded(entry)
                lost = missing.get((key, index))
                if lost is not None:
                    files = ", ".join(lost)
                    usage = entry.get("usage") or {}
                    if isinstance(figure, int) and not (usage.get("host") or usage.get("subagents")):
                        figure = unknown("its recorded usage holds no figure")
                    if isinstance(figure, dict):
                        figure = unknown(f"{figure['unknown']}; {files} is not on this machine, so the transcripts "
                                         "were not read for it")
                clash = overlapping(key, entry, others, labels) if isinstance(figure, int) else None
                if isinstance(figure, int) and clash is None and elsewhere is not None:
                    far = elsewhere_once()
                    if far[2] is not None:
                        figure = unknown(f"{far[2]}, so brackets of another slice that overlap this one cannot be "
                                         "ruled out and the transcripts are not on this machine")
                    else:
                        clash = overlapping(key, entry, far[0], far[1])
                if isinstance(figure, int) and clash is not None:
                    figure = unknown(f"brackets of {clash} overlap this one and the transcripts are not on this "
                                     "machine")
                shown[index] = {"tokens": figure, "delegates": [], "last_line": None, "searched": False}
            if not done:
                read["open"] += 1
            if shown[index]["searched"] and shown[index]["tokens"]:
                # the requests read into it are counted: they are in no other figure, so they stay in this one; an
                # open entry's are so far, and a same-second entry keeps them with its stage time unknown
                source = "transcripts" if done else "open"
            elif not done or entry.get("seconds") == 0:  # an open or unbracketed entry has no tokens to read
                shown[index]["tokens"] = recorded(entry)
            if not isinstance(shown[index]["tokens"], int):
                source = "unread"
            shown[index]["source"] = source
            if done or isinstance(shown[index]["tokens"], int):
                figures.append(shown[index]["tokens"])
                read["transcripts" if source == "open" else source] += 1
        bad = next((figure for figure in figures if isinstance(figure, dict)), None)
        result["records"][key] = {"entries": shown, "cost_read": read, "cost": {
            "tokens": bad if bad is not None else sum(figures) + loose[key], "shared": None,
            "sessions": {name: spent[key][name] for name in sorted(spent[key])}}}
    ran: dict[str, list[str]] = {}  # the features that ran in each session
    for key in keys:
        for name in used[key]:
            if str(by_key[key].get("feature")) not in ran.setdefault(name, []):
                ran[name].append(str(by_key[key].get("feature")))
    for name in ran:
        ran[name].sort()

    def part(name: str, feature: str) -> dict[str, Any]:
        """One feature's part of a session: the whole of it where it ran there alone; else the attributed tokens of
        its own records and the shared requests its brackets cover (the first feature, by name, where several
        cover one), the rest being `elsewhere` — other features' and no one's."""
        whole = summary[name]
        if len(ran[name]) < 2:
            return whole
        brackets = {other: [item for item in held if item.session == name and
                            str(by_key[item.path].get("feature")) == other] for other in ran[name]}
        shared = 0
        for request in shared_requests[name]:
            covered = [other for other in ran[name]
                       if any(item.window.covers(request.file, request.offset) for item in brackets[other])]
            if covered and covered[0] == feature:
                shared += request.tokens
        attributed = sum(spent[key].get(name, 0) for key in keys if str(by_key[key].get("feature")) == feature)
        return {"total": whole["total"], "attributed": attributed, "shared": shared,
                "elsewhere": whole["total"] - attributed - shared}

    for feature in {str(record.get("feature")) for record in by_key.values()}:
        members = [key for key in keys if str(by_key[key].get("feature")) == feature]
        names = sorted(set().union(*(used[key] for key in members)))
        refused = unknown("no transcript was read") if not names or absent(names) else None
        mine = {name: part(name, feature) for name in names if sessions[name].present}
        result["features"][feature] = {
            "sessions": {name: mine[name] if sessions[name].present else
                         dict.fromkeys(PARTS, unknown("the transcripts are not on this machine"))
                         for name in names},
            "notes": sorted({*(note for name in names for note in notes[name]),
                             *(f"{file} is not on this machine: the entries that span it are costed from their "
                               "recorded usage" for file in notes_gone),
                             *(f"session {name} also ran in feature {other}: its shared bucket is split by the "
                               "brackets that cover each request, and `elsewhere` is what this feature's records "
                               "and shared share do not hold" for name in names for other in ran[name]
                               if other != feature)}),
            "shared": refused if refused is not None else sum(mine[name]["shared"] for name in names)}
        for key in members:
            cost = result["records"][key]["cost"]
            if by_key[key].get("slice") is None:
                cost["shared"] = result["features"][feature]["shared"]
            elif not used[key] or absent(used[key]):
                cost["shared"] = unknown("no transcript was read")
            else:
                cost["shared"] = sum(
                    request.tokens for name in used[key] for request in shared_requests[name]
                    if any(item.window.covers(request.file, request.offset)
                           for item in held if item.path == key and item.session == name))
    return result
