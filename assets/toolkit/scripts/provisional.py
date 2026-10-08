"""Provisional decisions (S27, D195-D201): what an always-ask item becomes, and the gate's reading of its lines.

`python3 scripts/provisional.py status --decide <value> --ask no|approval|fact|must|release --when <ISO instant>
--number D<n> [--reversibility '<the Reversibility line, with or without its label>']` prints the `Status:` line a
decision entry carries (and, where provisional, its `Revert:` line), from the `decide` value of `.specify/cruise.json`
(passed, never read: the verb reads no file). Provisional is `provisional` with a final tier of easy or guarded and none
of `ci_workflow=yes`, `migrate_file=yes`, `flag_default=yes` (FR-033); a fact, a constitution MUST and a release are
unavailable whatever `decide` says. A missing `--reversibility` line is `hard`.
`python3 scripts/provisional.py audit [--feature <name>]` is the completion audit: it prints `cruise: parked: ratify
D<n> in specs/<feature>/decisions.md` and exits 3 while an entry of any feature's log has a first `Status` starting
with the word `provisional`, the lowest-numbered named; `--feature` only has to name a feature under `specs/`.
The gate (`check-decisions.py`) loads this file by path, only for a log carrying a `Status: provisional|ratified|
reverted` or a `Provisional (shadow|advisory):` line (a lone `Revert:` loads nothing, D206), and `check_log()` holds
those lines to their grammar.
Nothing here prints or exits outside `main`; `reversibility.py` beside this file is loaded by path, bytecode off.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from collections.abc import Iterable, Mapping
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

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
# D204: what a provisional or ratified entry's `Written to` may not name. A workflow, a control the runner parks on
# (`agents/cruise.py`'s CONTROL_PATHS, whether the delivery material is at the root or under `delivery/`), and a
# configuration file a generated gate reads: the list is closed, and a test holds it against what the starters ship.
CI_DIRECTORIES = (".github/workflows", ".gitea/workflows")
CONTROL_DIRECTORIES = ("scripts", "tools", "delivery/scripts", "delivery/Makefile", ".claude/settings.json")
CONTROL_FILES = ("Makefile", ".gitlab-ci.yml")
GATE_CONFIGURATION = re.compile(
    r"(?:biome\.jsonc?|tsconfig(?:\.[\w.-]+)?\.json|package(?:-lock)?\.json|(?:vite|vitest)(?:\.[\w-]+)?\.config\.\w+|"
    r"pyproject\.toml|uv\.lock|\.python-version|\.nvmrc|go\.(?:mod|sum|work)|\.gremlins\.ya?ml|\.golangci\.ya?ml|"
    r"pom\.xml|checkstyle\.xml|pmd-ruleset\.xml|spotbugs-exclude\.xml|maven-wrapper\.properties|\.editorconfig|"
    r"ruff\.toml|mypy\.ini|pytest\.ini|setup\.cfg|tox\.ini|\.importlinter|eslint\.config\.\w+|\.eslintrc(?:\.\w+)?)")
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


def utc_day(when: str) -> date | None:
    """The UTC calendar date of an ISO date or instant: a `T` or a space between date and time, `Z` or an offset
    (`+05:30`, `+0530`, `+05`) after it, none read as UTC. None where `when` is not one."""
    if len(when) <= 10:
        return calendar(when)
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
    return (instant.astimezone(timezone.utc) if instant.tzinfo else instant).date()


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


def protected(path: str) -> bool:
    """Whether `path` is a workflow, a control, a configuration file of a generated gate, or a directory holding one."""
    if path in ("", ".") or path.split("/")[-1] == "Makefile" or path in CONTROL_FILES:
        return True
    if any(path == name or path.startswith(name + "/") or name.startswith(path + "/")
           for name in CI_DIRECTORIES + CONTROL_DIRECTORIES):
        return True
    return GATE_CONFIGURATION.fullmatch(path.rsplit("/", 1)[-1]) is not None


def written_findings(where: str, fields: Mapping[str, str]) -> list[str]:
    """One finding naming the protected paths of an entry's `Written to`, whatever its declared facts say (D204)."""
    named = [path for path in written_to(fields.get("Written to", "")) if protected(path)]
    if not named:
        return []
    return [f"{where} `Written to` names {', '.join(f'`{path}`' for path in named)}, a workflow, a control of the "
            "run or a configuration file a generated gate reads; a provisional decision never edits one (D204)"]


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


def check_log(relative: str, items: Iterable[tuple[int, int | None, Mapping[str, str], set[str]]],
              ) -> list[str]:
    """The findings for one decisions log: `items` are (line, entry number or None, fields, repeated labels) as the
    gate parsed them. Each is `<file>:<line>: D<n> ...`, one per fault, naming the field."""
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
            findings += written_findings(where, fields) + reversibility_findings(where, fields)
        if sound and kind == "provisional":
            findings += date_findings(where, fields, status_date(fields["Status"]))
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


def status_verb(arguments: list[str]) -> int:
    options = parse_status(arguments)
    out, err = status_lines(options["--decide"], options["--ask"], options["--when"], options["--number"],
                            options.get("--reversibility"))
    print("\n".join(out))
    print("\n".join(err), file=sys.stderr)
    return 0


FIELD_LINE = re.compile(r"^- \*\*([^*]+):\*\* ?(.*)$")
HEADING = re.compile(r"^## D([0-9]+) — ")


def unratified(text: str) -> list[int]:
    """The numbers of the entries whose first `Status` starts with the word `provisional`, lowest first. A line is read
    as the gate reads it: split as `str.splitlines` splits, its label the text before the first colon, stripped."""
    found: list[int] = []
    number, seen = None, False
    for line in text.removeprefix("\ufeff").splitlines():
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
