"""Provisional decisions (S27, D195-D201): what an always-ask item becomes, and the gate's reading of its lines.

`python3 scripts/provisional.py status --decide <value> --ask no|approval|fact|must|release --when <ISO instant>
--number D<n> [--reversibility '<the Reversibility line, with or without its label>']` prints the `Status:` line a
decision entry carries (and, where provisional, its `Revert:` line), from the `decide` value of `.specify/cruise.json`
(passed, never read: the verb reads no file). Provisional is `provisional` with a final tier of easy or guarded and none
of `ci_workflow=yes`, `migrate_file=yes`, `flag_default=yes` (FR-033); a fact, a constitution MUST and a release are
unavailable whatever `decide` says. A missing `--reversibility` line is `hard`.
`python3 scripts/provisional.py audit [--feature <name>]` is the completion audit: it prints `cruise: parked: ratify
D<n>` and exits 3 while an entry of `specs/<feature>/decisions.md` has a first `Status` starting `provisional`.
The gate (`check-decisions.py`) loads this file by path, only for a log carrying a `Status: provisional|ratified|
reverted`, a `Revert:` or a `Provisional (shadow|advisory):` line, and `check_log()` holds those lines to their grammar.
Nothing here prints or exits outside `main`; `reversibility.py` beside this file is loaded by path, bytecode off.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from collections.abc import Iterable, Mapping
from datetime import date, timedelta
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


def ratify_by(when: str) -> str:
    """The date a provisional decision is ratified by: the `When` instant's calendar date plus seven days (D199)."""
    day = calendar(when[:10])
    if day is None:
        raise Usage(f"--when {when!r} does not start with an ISO date (YYYY-MM-DD)")
    return (day + timedelta(days=7)).isoformat()


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
        if sound and kind == "provisional":
            findings += reversibility_findings(where, fields)
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


STATUS_LINE = re.compile(r"^- \*\*Status:\*\* ?(.*)$")
HEADING = re.compile(r"^## D([0-9]+) — ")


def unratified(text: str) -> list[int]:
    """The numbers of the entries whose first `Status` starts with `provisional`, lowest first."""
    found: list[int] = []
    number, seen = None, False
    for line in text.removeprefix("\ufeff").split("\n"):
        heading = HEADING.match(line)
        if line.startswith("## "):
            number, seen = int(heading.group(1)) if heading else None, False
        elif number is not None and not seen and (status := STATUS_LINE.match(line)):
            seen = True
            if status.group(1).strip().startswith("provisional"):
                found.append(number)
    return sorted(found)


def project_root(script: Path) -> Path:
    """The nearest parent of this script holding `project.json`, as the gate finds it."""
    return next((parent for parent in script.parents if (parent / "project.json").is_file()), script.parents[1])


def audit_verb(arguments: list[str]) -> int:
    """`audit [--feature <name>]`: exit 3, `cruise: parked: ratify D<n>`, while a provisional decision is unratified."""
    if arguments and (len(arguments) != 2 or arguments[0] != "--feature" or not arguments[1]):
        raise Usage("audit takes only --feature <name>, once")
    specs = project_root(Path(__file__).resolve()) / "specs"
    logs = sorted(specs.glob("*/decisions.md")) if specs.is_dir() else []
    if arguments:
        logs = [log for log in logs if log.parent.name == arguments[1]]
    elif len(logs) > 1:
        raise Usage("specs/ holds several decisions.md; choose one with --feature <name>: "
                    + ", ".join(log.parent.name for log in logs))
    if not logs:
        print("provisional: no decisions.md, so no unratified provisional decision")
        return 0
    relative = logs[0].relative_to(specs.parent).as_posix()
    try:
        waiting = unratified(logs[0].read_text(encoding="utf-8"))
    except UnicodeDecodeError as error:
        print(f"provisional: {relative}: not UTF-8 ({error.reason} at byte {error.start})", file=sys.stderr)
        return 1
    if waiting:
        print(f"cruise: parked: ratify D{waiting[0]}")
        return 3
    print(f"provisional: no unratified provisional decision in {relative}")
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
