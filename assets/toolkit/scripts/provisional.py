"""Provisional decisions (S27, D195-D201): what an always-ask item becomes, and the gate's reading of its lines.

`python3 scripts/provisional.py status --decide <value> --ask no|approval|fact|must|release --when <ISO instant>
--number D<n> [--reversibility '<the Reversibility line, with or without its label>']` prints the `Status:` line a
decision entry carries (and, where provisional, its `Revert:` line), for the `decide` value of `.specify/cruise.json`
(passed, and refused with exit 2 where it differs from the file's, D209; no file is no check). Provisional is `provisional` with a final tier of easy or guarded and none
of `ci_workflow=yes`, `migrate_file=yes`, `flag_default=yes` (FR-033); a fact, a constitution MUST and a release are
unavailable whatever `decide` says. A missing `--reversibility` line is `hard`.
`python3 scripts/provisional.py audit [--feature <name>]` is the completion audit: it prints `cruise: parked: ratify
D<n> in specs/<feature>/decisions.md` and exits 3 while an entry of any feature's log has a first `Status` starting
with the word `provisional`, the lowest-numbered named, in the log as `reading` gives it (fences and near-miss labels
blanked, ASCII digits in a heading: the text the gate reads, D210); `--feature` only has to name a feature under `specs/`.
The gate (`check-decisions.py`) loads this file by path, only for a log carrying a `Status: provisional|ratified|
reverted` or a `Provisional (shadow|advisory):` line (a lone `Revert:` loads nothing, D206), and `check_log()` holds
those lines to their grammar, reads them from one reading of the log (`reading`, D210), refuses a mode entry dated after
the gate runs and a provisional `Status` that no mode entry to `provisional` precedes in any feature's log (D209).
Nothing here prints or exits outside `main`; `reversibility.py` beside this file is loaded by path, bytecode off.
"""
from __future__ import annotations

import importlib.util
import json
import posixpath
import re
import sys
from collections.abc import Collection, Iterable, Mapping
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, NamedTuple

DECIDE = ("recommended-first", "skipper-always", "provisional-shadow", "provisional-advisory", "provisional")
ASKS = ("no", "approval", "fact", "must", "release")
HELD_FACTS = ("ci_workflow", "migrate_file", "flag_default")
MODE_LINES = ("provisional-shadow", "provisional-advisory")
UNAVAILABLE = "unavailable: "
APPROVAL = "a person's approval"
STANDING = "- **Status:** standing"
REASONS = {"fact": "a fact nobody here has", "must": "an option that breaks a constitution MUST",
           "release": "a release nobody asked for"}
HELD_WHY = {"ci_workflow": "provisional approval never edits a workflow", "flag_default": "provisional approval never "
            "flips a flag", "migrate_file": "provisional approval never edits a migrate-propagated file"}
OPTIONS = ("--decide", "--ask", "--when", "--number", "--reversibility")
REQUIRED = OPTIONS[:4]
DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
NUMBER = re.compile(r"D[1-9][0-9]*")
USAGE = ("usage: provisional.py status --decide <" + "|".join(DECIDE) + "> --ask <" + "|".join(ASKS) +
         "> --when <ISO instant> --number D<n> [--reversibility '<line>']"
         " | audit [--feature <name>]")


FORMS = ("provisional", "ratified", "reverted")
STATUS_FORM = re.compile(r"provisional · ratify by ([0-9]{4}-[0-9]{2}-[0-9]{2})|(?:ratified|reverted) "
                         r"([0-9]{4}-[0-9]{2}-[0-9]{2})")
MODE_LABELS = ("Provisional (shadow)", "Provisional (advisory)")
REHEARSAL_FORM = re.compile(r"(easy|guarded|hard) · (provisional · ratify by ([0-9]{4}-[0-9]{2}-[0-9]{2})|"
                            r"blocks \(hard\)|blocks \((?:ci_workflow|migrate_file|flag_default)=yes\)) · Revert: "
                            r"commits carrying Decision: D([1-9][0-9]*)")
# D204, D210: what a provisional or ratified entry's `Written to` may not name. A workflow, a control the runner parks on
# (`agents/cruise.py`'s CONTROL_PATHS, whether the delivery material is at the root or under `delivery/`, and the hook
# file of every harness whose registry row projects one), the delivery directory an adopted project keeps its material
# in (its scripts, Makefile and `.written`), and a configuration file a generated gate reads: the list is closed, and a
# test holds it against what the starters ship and what the registry projects. Names compare in any case, the way the
# committed list of S26 does. Each is written as its segments: the scoped gate reads a whole path in a check's script as
# a file the check reads.
CI_DIRECTORIES = tuple("/".join(parts) for parts in ((".github", "workflows"), (".gitea", "workflows")))
CONTROL_DIRECTORIES = tuple("/".join(parts) for parts in (
    ("scripts",), ("tools",), ("delivery", "scripts"), ("delivery", "Makefile"), (".claude", "settings.json"),
    (".cursor", "hooks.json"), (".gemini", "settings.json"), (".slipwai", "propagated")))
CONTROL_FILES = ("Makefile", "GNUmakefile", "makefile", ".gitlab-ci.yml")
DELIVERY_PARTS = ("scripts", "Makefile", ".written")  # under an adopted project's `layout.delivery`
GATE_CONFIGURATION = re.compile(
    r"(?:biome\.jsonc?|tsconfig(?:\.[\w.-]+)?\.json|package(?:-lock)?\.json|(?:vite|vitest)(?:\.[\w-]+)?\.config\.\w+|"
    r"pyproject\.toml|uv\.lock|\.python-version|\.nvmrc|go\.(?:mod|sum|work)|\.gremlins\.ya?ml|\.golangci\.ya?ml|"
    r"pom\.xml|checkstyle\.xml|pmd-ruleset\.xml|spotbugs-exclude\.xml|maven-wrapper\.properties|\.editorconfig|"
    r"\.?ruff\.toml|mypy\.ini|pytest\.ini|setup\.cfg|tox\.ini|\.importlinter|eslint\.config\.\w+|"
    r"\.eslintrc(?:\.\w+)?|conftest\.py|[\w.-]*flags[\w.-]*\.tfvars)", re.I)
REVERT_FORM = re.compile(r"commits carrying Decision: D([1-9][0-9]*)")


class Usage(Exception):
    """A call the verb does not understand: one line naming the option, exit 2."""


def calendar(text: str) -> date | None:
    """The date `text` spells as `YYYY-MM-DD`, or None where it is not a calendar date."""
    if DATE.fullmatch(text):
        try:
            return date.fromisoformat(text)
        except ValueError:
            return None
    return None


def instant_of(when: str) -> datetime | None:
    """The UTC instant of an ISO date or instant: a `T` or a space between date and time, `Z` or an offset
    (`+05:30`, `+0530`, `+05`) after it, none read as UTC, a date alone as its midnight. None where `when` is not one."""
    if len(when) <= 10:
        day = calendar(when)
        return None if day is None else datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    if calendar(when[:10]) is None:
        return None
    tail = when[10:].strip() if when[10] == " " else when[10:]
    tail = re.sub(r"Z$", "+00:00", tail, flags=re.I)
    tail = re.sub(r"([+-][0-9]{2})([0-9]{2})$", r"\1:\2", tail)
    tail = re.sub(r"([+-][0-9]{2})$", r"\1:00", tail)
    try:
        instant = datetime.fromisoformat(when[:10] + (" " if tail[:1] not in ("T", "t") else "") + tail)
    except ValueError:
        return None
    return instant.astimezone(timezone.utc) if instant.tzinfo else instant.replace(tzinfo=timezone.utc)


def utc_day(when: str) -> date | None:
    """The UTC calendar date of an ISO date or instant (`instant_of`); None where `when` is not one."""
    instant = instant_of(when)
    return None if instant is None else instant.date()


def ratify_by(when: str) -> str:
    """The date a provisional decision is ratified by: the `When` instant's UTC calendar date plus seven days (D199).
    An instant with an offset is converted to UTC first; `Z`, no offset and a date alone keep their own date."""
    day = utc_day(when)
    if day is None:
        raise Usage(f"--when {when!r} is not an ISO date or instant (YYYY-MM-DD, then optionally T or a space, a time "
                    "and Z or an offset)")
    return (day + timedelta(days=7)).isoformat()


def status_date(status: str) -> str:
    """The ratify-by date of a well-formed `provisional · ratify by YYYY-MM-DD`."""
    return status.rsplit(" ", 1)[-1]


def date_findings(where: str, fields: Mapping[str, str], until: str) -> list[str]:
    """The finding for a provisional entry whose ratify-by date is not its `When` date plus seven days, UTC (D205)."""
    found = re.search(r"\*\*When:\*\* (.+?)\s*(?: · |$)", fields.get("Stage", ""))
    day = utc_day(found.group(1)) if found else None
    if day is None:
        return [f"{where} `Status` cannot be checked: the `Stage` line has no `When` that is an ISO date or instant"]
    expected = (day + timedelta(days=7)).isoformat()
    if until == expected:
        return []
    return [f"{where} `Status` ratifies by {until}; it is the `When` date plus seven days, UTC: {expected} (D199)"]


def written_to(value: str) -> list[str]:
    """The paths a `Written to` line names: backticked, or comma-separated bare, each as a relative posix path."""
    names = re.findall(r"`([^`]+)`", value) or value.split(",")
    return [name.strip().replace("\\", "/").removeprefix("./").rstrip("/") for name in names if name.strip()]


def delivery_directory(root: Path) -> str | None:
    """The directory an adopted project keeps its delivery material in (`layout.delivery` of `project.json`), as a
    project-relative path (`.` for the root, where it names none); None where the project is not adopted."""
    try:
        document = json.loads((root / "project.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(document, dict) or document.get("origin") != "adopted":
        return None
    layout = document.get("layout")
    named = layout.get("delivery", ".") if isinstance(layout, dict) else "."
    folded = posixpath.normpath(named.replace("\\", "/")) if isinstance(named, str) else "."
    return "." if posixpath.isabs(folded) or folded.split("/")[0] == ".." else folded


def protected(path: str, delivery: str | None = None) -> bool:
    """Whether `path`, a project-relative posix path, is a workflow, a control, a configuration file of a generated gate,
    or a directory holding one; `delivery` is an adopted project's delivery directory, whose scripts, Makefile and
    `.written` are controls too. Names compare in any case."""
    path = path.casefold()
    if path in ("", ".") or path.split("/")[-1] in {name.casefold() for name in CONTROL_FILES} or ".mvn" in path.split("/"):
        return True
    names = [name.casefold() for name in CI_DIRECTORIES + CONTROL_DIRECTORIES]
    names += [posixpath.join(delivery, part).removeprefix("./").casefold() for part in DELIVERY_PARTS] if delivery else []
    if any(path == name or path.startswith(name + "/") or name.startswith(path + "/") for name in names):
        return True
    return GATE_CONFIGURATION.fullmatch(path.rsplit("/", 1)[-1]) is not None


def named_paths(value: str, root: Path) -> list[str]:
    """Every project-relative path a `Written to` value names, as S26 reads one (`written_paths`: backticked, bare beside
    them, separated by `,`, `;` or `and`) and resolves it (`inside`: absolute inside the project, `..`, `//`, `./`);
    a path that lands outside the project is no path in it."""
    try:
        module = reversibility_module()
    except OSError:  # the gate says reversibility.py is missing in its own finding
        return written_to(value)
    return [path for path in (module.inside(name, root) for name in module.written_paths(value)) if path]


def written_findings(where: str, fields: Mapping[str, str], twice: Collection[str] = ()) -> list[str]:
    """The findings for an entry's `Written to`: said once, and no protected path in it, whatever its declared facts say
    (D204, D210)."""
    found = []
    if "Written to" in twice:
        found.append(f"{where} `Written to` is on more than one line; a provisional or ratified entry says it once, "
                     "because only the first is read (D210)")
    root = project_root(Path(__file__).resolve())
    delivery = delivery_directory(root)
    named = [path for path in dict.fromkeys(named_paths(fields.get("Written to", ""), root)) if protected(path, delivery)]
    if named:
        found.append(f"{where} `Written to` names {', '.join(f'`{path}`' for path in named)}, a workflow, a control of "
                     "the run or a configuration file a generated gate reads; a provisional decision never edits one "
                     "(D204)")
    return found


def reversibility_module() -> Any:
    """`reversibility.py` beside this file, loaded by path with bytecode off."""
    sys.dont_write_bytecode = True
    path = Path(__file__).resolve().with_name("reversibility.py")
    spec = importlib.util.spec_from_file_location("reversibility", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def final_tier(value: str | None) -> tuple[str, dict[str, str]]:
    """(final tier, facts) of a `Reversibility:` line with or without its label; no line is `hard` with no facts."""
    if value is None:
        return "hard", {}
    module = reversibility_module()
    try:
        tiers, _, facts = module.parse_line(value.strip().removeprefix(module.LABEL.strip()).strip())
    except ValueError as error:
        raise Usage(f"--reversibility {error}") from error
    return tiers[-1], facts


def held_fact(facts: dict[str, str]) -> str | None:
    """The first of the three facts FR-033 holds back that the line says `yes` to."""
    return next((fact for fact in HELD_FACTS if facts.get(fact) == "yes"), None)


def rehearsal(decide: str, tier: str, held: str | None, until: str, number: str) -> str:
    """The `Provisional (shadow|advisory):` line: the final tier, what `provisional` would have done, the revert."""
    would = f"provisional · ratify by {until}"
    if tier == "hard" or held:
        would = "blocks (hard)" if tier == "hard" else f"blocks ({held}=yes)"
    label = "advisory" if decide == "provisional-advisory" else "shadow"
    return f"- **Provisional ({label}):** {tier} · {would} · Revert: commits carrying Decision: {number}"


def status_lines(decide: str, ask: str, when: str, number: str, line: str | None) -> tuple[list[str], list[str]]:
    """(stdout lines, stderr lines) of the verb for these inputs."""
    if ask == "no":
        return [STANDING], ["provisional: nothing asked of a person"]
    if ask != "approval":
        return ([UNAVAILABLE + REASONS[ask], STANDING],
                [f"provisional: unavailable - {REASONS[ask]}, whatever decide says"])
    tier, facts = final_tier(line)
    held, until = held_fact(facts), ratify_by(when)
    if tier == "hard":
        why = "hard: " + ("no Reversibility line, so hard" if line is None else "the final tier is hard")
    elif held is not None:
        why = f"{held}=yes: {HELD_WHY[held]} (FR-033)"
    elif decide == "provisional":
        revert = f"- **Revert:** commits carrying Decision: {number}"
        return ([f"- **Status:** provisional · ratify by {until}", revert],
                [f"provisional: {tier}, no held fact; provisional until ratified by {until}"])
    else:
        why = f"decide is {decide}"
    out, err = [UNAVAILABLE + APPROVAL], [f"provisional: unavailable - {why}"]
    if decide in MODE_LINES:
        out.append(rehearsal(decide, tier, held, until, number))
        if decide == "provisional-advisory" and tier != "hard" and held is None:
            err.append(f"cruise: parked: {number} needs a person's approval; recommended: provisional · ratify by "
                       f"{until} ({tier}) — answer accept through /cruise-tell")
    return [*out, STANDING], err


def status_kind(fields: Mapping[str, str]) -> str:
    """The first word of an entry's `Status` where it is one of the three this module reads, else the empty string."""
    words = fields.get("Status", "").split()
    return words[0] if words and words[0] in FORMS else ""


def well_formed(status: str) -> bool:
    """Whether `status` is exactly one of the three forms, its date a calendar date."""
    found = STATUS_FORM.fullmatch(status)
    return found is not None and calendar(found.group(1) or found.group(2)) is not None


def revert_findings(where: str, number: int, fields: Mapping[str, str], twice: set[str], kind: str) -> list[str]:
    """The findings for one entry's `Revert:` line: said once, only by a provisional, ratified or reverted entry, and
    `commits carrying Decision: D<own number>`; a provisional entry must say it."""
    found = [f"{where} `Revert` is on more than one line; an entry says it once"] if "Revert" in twice else []
    if "Revert" not in fields:
        return found
    if not kind:
        return found + [f"{where} `Revert` is on an entry whose `Status` is {fields.get('Status', '')!r}; only a "
                        "provisional, ratified or reverted entry carries one"]
    named = REVERT_FORM.fullmatch(fields["Revert"])
    if named is None:
        return found + [f"{where} `Revert` is {fields['Revert']!r}; it is `commits carrying Decision: D{number}`"]
    if int(named.group(1)) != number:
        found.append(f"{where} `Revert` names D{named.group(1)}; it names this entry, D{number}")
    return found


def reversibility_findings(where: str, fields: Mapping[str, str]) -> list[str]:
    """What FR-033 asks of a provisional entry's `Reversibility:` line: it has one, it does not end at `hard`, and none
    of the three facts is `yes` (one finding per fact). A line `reversibility.py` cannot read is its finding."""
    if "Reversibility" not in fields:
        return [f"{where} `Reversibility` is missing; a provisional entry is scored, and no score is hard"]
    try:
        tiers, _, facts = reversibility_module().parse_line(fields["Reversibility"])
    except ValueError:
        return []
    except OSError:
        return [f"{where} `Reversibility` cannot be held: reversibility.py is not beside this script"]
    found = []
    if tiers[-1] == "hard":
        found.append(f"{where} `Reversibility` ends at hard; a hard decision is never provisional")
    return found + [f"{where} `Reversibility` has {fact}=yes; {HELD_WHY[fact]} (FR-033)" for fact in HELD_FACTS
                    if facts.get(fact) == "yes"]


def rehearsal_findings(where: str, number: int, fields: Mapping[str, str], twice: set[str]) -> list[str]:
    """The findings for an entry's `Provisional (shadow|advisory):` lines: at most one of either label, each
    `<tier> · <would-have> · Revert: commits carrying Decision: D<own>` with `blocks (hard)` exactly for `hard`."""
    labels = [label for label in MODE_LABELS if label in fields]
    found = []
    if len(labels) > 1 or twice & set(MODE_LABELS):
        found.append(f"{where} `{(labels or MODE_LABELS)[0]}` is a second rehearsal line; an entry has at most one")
    for label in labels:
        value = fields[label]
        parts = REHEARSAL_FORM.fullmatch(value)
        problem = ""
        if parts is None:
            problem = ("is not `<tier> · provisional · ratify by YYYY-MM-DD | blocks (hard) | blocks (<fact>=yes) · "
                       f"Revert: commits carrying Decision: D{number}`")
        elif parts.group(3) is not None and calendar(parts.group(3)) is None:
            problem = f"has {parts.group(3)!r}, which is not a calendar date"
        elif (parts.group(2) == "blocks (hard)") != (parts.group(1) == "hard"):
            problem = "says `blocks (hard)` exactly when the tier is hard"
        elif int(parts.group(4)) != number:
            problem = f"has a Revert naming D{parts.group(4)}; it names this entry, D{number}"
        if problem:
            found.append(f"{where} `{label}` {problem}: {value!r}")
    return found


class Mode(NamedTuple):
    """One mode entry (`## D<n> — decide moved from <a> to <b>`, written by `cruise.py mode`): where, and when."""
    relative: str
    line: int
    number: int
    when: str
    instant: datetime | None
    to: str


MODE_HEADING = re.compile(r"^## D([0-9]+) — decide moved from (\S+) to (\S+)\s*$")
WHEN_FIELD = re.compile(r"\*\*When:\*\* (\S+)")


def mode_entries(relative: str, view: str) -> list[Mode]:
    """The mode entries of a log as `reading` gives it, each with the instant its Stage line's `When` is (None where it
    is no ISO date or instant)."""
    found: list[Mode] = []
    heading: re.Match[str] | None = None
    for number, line in enumerate(view.splitlines(), start=1):
        if line.startswith("## "):
            heading = MODE_HEADING.match(line)
            if heading:
                found.append(Mode(relative, number, int(heading.group(1)), "", None, heading.group(3)))
        elif heading and not found[-1].when and (stamp := WHEN_FIELD.search(line)) and line.startswith("- **Stage:**"):
            found[-1] = found[-1]._replace(when=stamp.group(1), instant=instant_of(stamp.group(1)))
    return found


def mode_findings(modes: Iterable[Mode], now: datetime) -> list[str]:
    """One finding for each mode entry dated after `now`: a mode entry is dated when it is written, and one dated ahead
    would stand as the last for ever (D209)."""
    return [f"{mode.relative}:{mode.line}: D{mode.number} (decide moved to {mode.to}) is dated {mode.when}, after now; a "
            "mode entry is dated when it is written, and one dated ahead is no record of what was in force (D209)"
            for mode in modes if mode.instant is not None and mode.instant > now]


def basis_findings(where: str, fields: Mapping[str, str], modes: Iterable[Mode], now: datetime) -> list[str]:
    """The finding for a provisional entry that no climb to `provisional` stands behind: the last mode entry of any
    feature's log dated at or before its `When` (and not after `now`) has to record `provisional` (D209)."""
    found = re.search(r"\*\*When:\*\* (.+?)\s*(?: · |$)", fields.get("Stage", ""))
    when = instant_of(found.group(1)) if found else None
    if when is None:  # `date_findings` says so
        return []
    earlier = [mode for mode in modes if mode.instant is not None and mode.instant <= min(when, now)]
    last = max(earlier, key=lambda mode: (mode.instant, mode.relative, mode.line), default=None)
    if last is not None and last.to == "provisional":
        return []
    said = f"the last, {last.relative}:{last.line}, records `{last.to}`" if last else "there is none"
    return [f"{where} `Status` is provisional, but no mode entry in any feature's log puts `decide` at `provisional` "
            f"before its `When`: {said}; a provisional entry follows a person's climb to `provisional`, which `cruise.py "
            "mode` writes down (D209)"]


def check_log(relative: str, items: Iterable[tuple[int, int | None, Mapping[str, str], set[str]]],
              modes: Iterable[Mode], now: datetime) -> list[str]:
    """The findings for one decisions log: `items` are (line, entry number or None, fields, repeated labels) as the
    gate parsed them; `modes` are the mode entries of every feature's log. Each is `<file>:<line>: D<n> ...`, one per
    fault, naming the field."""
    modes = list(modes)
    findings: list[str] = []
    for line, number, fields, twice in items:
        if number is None:
            continue
        where = f"{relative}:{line}: D{number}"
        kind = status_kind(fields)
        sound = kind == "" or well_formed(fields["Status"])
        if not sound:
            findings.append(f"{where} `Status` is {fields['Status']!r}; it is `provisional · ratify by YYYY-MM-DD`, "
                            "`ratified YYYY-MM-DD` or `reverted YYYY-MM-DD`, a calendar date")
        findings += revert_findings(where, number, fields, twice, kind)
        if sound and kind == "provisional" and "Revert" not in fields:
            findings.append(f"{where} `Revert` is missing; a provisional entry says `commits carrying Decision: "
                            f"D{number}`")
        if sound and kind in ("provisional", "ratified"):
            findings += written_findings(where, fields, twice) + reversibility_findings(where, fields)
        if sound and kind == "provisional":
            findings += date_findings(where, fields, status_date(fields["Status"])) + basis_findings(where, fields,
                                                                                                    modes, now)
        findings += rehearsal_findings(where, number, fields, twice)
    return findings


def parse_status(arguments: list[str]) -> dict[str, str]:
    """The verb's options, each once; Usage names the one at fault."""
    options: dict[str, str] = {}
    rest = iter(arguments)
    for argument in rest:
        if argument not in OPTIONS:
            raise Usage(f"{argument!r} is not an option of status ({', '.join(OPTIONS)})")
        value = next(rest, None)
        if value is None or argument in options:
            raise Usage(f"{argument} needs one value, once")
        options[argument] = value
    for option in REQUIRED:
        if option not in options:
            raise Usage(f"{option} is required")
    for option, accepted in (("--decide", DECIDE), ("--ask", ASKS)):
        if options[option] not in accepted:
            raise Usage(f"{option} {options[option]!r} is not one of {', '.join(accepted)}")
    if not NUMBER.fullmatch(options["--number"]):
        raise Usage(f"--number {options['--number']!r} is not D<n>")
    ratify_by(options["--when"])
    return options


CONFIG_PARTS = (".specify", "cruise.json")


def configured_decide(root: Path) -> str | None:
    """The `decide` of the project's `.specify/cruise.json`: the bottom rung where the file names none or a value that
    is not one of the five (as `cruise.py` reads it), None where there is no file. A file that cannot be read is Usage."""
    path = root.joinpath(*CONFIG_PARTS)
    if not path.is_file():
        return None
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Usage(f"{'/'.join(CONFIG_PARTS)} cannot be read ({error}); --decide is the file's value") from error
    if not isinstance(document, dict):
        raise Usage(f"{'/'.join(CONFIG_PARTS)} is not a JSON object; --decide is the file's value")
    return document["decide"] if document.get("decide") in DECIDE else DECIDE[0]


def status_verb(arguments: list[str]) -> int:
    options = parse_status(arguments)
    configured = configured_decide(project_root(Path(__file__).resolve()))
    if configured is not None and options["--decide"] != configured:
        raise Usage(f"--decide {options['--decide']!r} is not the `decide` of {'/'.join(CONFIG_PARTS)}, "
                    f"{configured!r}; the verb takes it from the file (D209)")
    out, err = status_lines(options["--decide"], options["--ask"], options["--when"], options["--number"],
                            options.get("--reversibility"))
    print("\n".join(out))
    print("\n".join(err), file=sys.stderr)
    return 0


FIELD_LINE = re.compile(r"^- \*\*([^*]+):\*\* ?(.*)$")
HEADING = re.compile(r"^## D([0-9]+) — ")
ANY_HEADING = re.compile(r"^## D(\d+) — ")  # `\d` reads a fullwidth digit: the gate's heading, not the audit's
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
# A label written nearly right (another case, a space before the colon, underscores, another bullet): never read.
NEAR_LABEL = re.compile(r"^\s*[-*+]\s*[*_]*\s*(?:reversibility|proposed\s*rule|status)\s*[*_]*\s*:[*_]*", re.I)
EXACT_LABEL = re.compile(r"^- \*\*(?:Reversibility|Proposed rule|Status):\*\*")
STATUS_LABEL = re.compile(r"^- \*\*Status:\*\*[^\S\n]*(?:provisional|ratified|reverted)\b|"
                          r"^- \*\*Provisional \((?:shadow|advisory)\):\*\*", re.M)


def reading(text: str) -> tuple[str, list[tuple[int, str, str]]]:
    """The one reading of a log (D210): `text` with every line inside a ``` or ~~~ fence emptied, and every line whose
    label is nearly `- **Reversibility:**`, `- **Proposed rule:**` or `- **Status:**` emptied, line endings kept so
    every line number stands; and the near-miss lines as (line, entry, the label as written), each entry named `D<n>`
    where a heading above it has one. A fence closes on its own character, at least as long; one left open runs on.
    The gate decides to hold a log, reads its fields, and the audit finds its provisional entries, all from this."""
    kept: list[str] = []
    near: list[tuple[int, str, str]] = []
    opened, where = "", ""
    for number, piece in enumerate(text.splitlines(keepends=True), start=1):
        content = piece.splitlines()[0] if piece.splitlines() else ""
        fence = FENCE.match(content)
        hidden = bool(opened)
        if opened and fence and fence.group(1)[0] == opened[0] and len(fence.group(1)) >= len(opened) \
                and not content.strip().strip(opened[0]):
            opened = ""
        elif not opened and fence:
            opened, hidden = fence.group(1), True
        if not hidden:
            if content.startswith("## "):
                heading = ANY_HEADING.match(content)
                where = f"D{heading.group(1)}" if heading else ""
            label = NEAR_LABEL.match(content)
            if label and not EXACT_LABEL.match(content):
                near.append((number, where, label.group(0).strip()))
                hidden = True
        kept.append(piece[len(content):] if hidden else piece)
    return "".join(kept), near


def moded(view: str) -> bool:
    """Whether a log, as `reading` gave it, has a mode entry."""
    return any(MODE_HEADING.match(line) for line in view.splitlines())


def held(view: str) -> bool:
    """Whether a log, as `reading` gave it, carries a line only this module reads: a `Status` of one of the three new
    forms or a `Provisional (shadow|advisory):` line (a lone `Revert:` is not one, D206)."""
    return STATUS_LABEL.search(view) is not None


def reading_findings(relative: str, text: str) -> list[str]:
    """What a held log's reading refuses in itself: a near-miss `Status` label, which no reader takes for the entry's,
    and a heading whose number is spelled with a digit that is not 0-9 (which the audit cannot read)."""
    view, near = reading(text)
    found = [f"{relative}:{line}: {where or 'a line'} has `{label}`, which is not the label `- **Status:**` (or "
             "`- **Reversibility:**`, `- **Proposed rule:**`); a log that holds a provisional form reads no other "
             "spelling (D210)" for line, where, label in near if "status" in label.casefold()]
    for number, line in enumerate(view.splitlines(), start=1):
        heading = ANY_HEADING.match(line)
        if heading and not HEADING.match(line):
            found.append(f"{relative}:{number}: the heading `{line[:24]}` spells its number with a digit that is not "
                         "0-9; a log that holds a provisional form reads ASCII digits in a heading (D210)")
    return found


def unratified(text: str) -> list[int]:
    """The numbers of the entries whose first `Status` starts with the word `provisional`, lowest first, in the log as
    `reading` gives it. A line is read as the gate reads it: split as `str.splitlines` splits, its label the text before
    the first colon, stripped."""
    found: list[int] = []
    number, seen = None, False
    for line in reading(text.removeprefix("\ufeff"))[0].splitlines():
        heading = HEADING.match(line)
        if line.startswith("## "):
            number, seen = int(heading.group(1)) if heading else None, False
        elif number is not None and not seen and (field := FIELD_LINE.match(line)) \
                and field.group(1).split(":")[0].strip() == "Status":
            seen = True
            if field.group(2).split()[:1] == ["provisional"]:
                found.append(number)
    return sorted(found)


def project_root(script: Path) -> Path:
    """The nearest parent of this script holding `project.json`, as the gate finds it."""
    return next((parent for parent in script.parents if (parent / "project.json").is_file()), script.parents[1])


def audit_verb(arguments: list[str]) -> int:
    """`audit [--feature <name>]`: exit 3, `cruise: parked: ratify D<n> in <log>`, while any feature's log holds an
    unratified provisional decision, the lowest-numbered named (D207). `--feature` must name a directory of `specs/`
    and changes nothing else: the run is not done while any feature's decision stands provisional."""
    if arguments and (len(arguments) != 2 or arguments[0] != "--feature" or not arguments[1]):
        raise Usage("audit takes only --feature <name>, once")
    specs = project_root(Path(__file__).resolve()) / "specs"
    if arguments and not (specs / arguments[1]).is_dir():
        raise Usage(f"specs/{arguments[1]}/ is no directory; --feature names a feature under specs/")
    logs = sorted(specs.glob("*/decisions.md")) if specs.is_dir() else []
    if not logs:
        print("provisional: no decisions.md, so no unratified provisional decision")
        return 0
    waiting: list[tuple[int, str, str]] = []
    for log in logs:
        relative = log.relative_to(specs.parent).as_posix()
        try:
            waiting += [(number, log.parent.name, relative) for number in unratified(log.read_text(encoding="utf-8"))]
        except UnicodeDecodeError as error:
            print(f"provisional: {relative}: not UTF-8 ({error.reason} at byte {error.start})", file=sys.stderr)
            return 1
    if waiting:
        number, _, relative = min(waiting)
        print(f"cruise: parked: ratify D{number} in {relative}")
        return 3
    print("provisional: no unratified provisional decision in "
          + ", ".join(log.relative_to(specs.parent).as_posix() for log in logs))
    return 0


VERBS = {"status": status_verb, "audit": audit_verb}


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")  # the lines carry `·`; a pipe may not
    arguments = sys.argv[1:]
    try:
        if not arguments or arguments[0] not in VERBS:
            raise Usage(f"the verb is one of {', '.join(VERBS)}")
        return VERBS[arguments[0]](arguments[1:])
    except Usage as error:
        print(f"provisional: {error}\n{USAGE}".replace("\n", " - ", 1), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
