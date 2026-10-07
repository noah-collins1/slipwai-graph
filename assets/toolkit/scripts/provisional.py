"""Provisional decisions (S27, D195-D201): what an always-ask item becomes, and the gate's reading of its lines.

`python3 scripts/provisional.py status --decide <value> --ask no|approval|fact|must|release --when <ISO instant>
--number D<n> [--reversibility '<the Reversibility line, with or without its label>']` prints the `Status:` line a
decision entry carries (and, where provisional, its `Revert:` line), from the `decide` value of `.specify/cruise.json`
(passed, never read: the verb reads no file). Provisional is `provisional` with a final tier of easy or guarded and none
of `ci_workflow=yes`, `migrate_file=yes`, `flag_default=yes` (FR-033); a fact, a constitution MUST and a release are
unavailable whatever `decide` says. A missing `--reversibility` line is `hard`.
Nothing here prints or exits outside `main`; `reversibility.py` beside this file is loaded by path, bytecode off.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

DECIDE = ("recommended-first", "skipper-always", "provisional-shadow", "provisional-advisory", "provisional")
ASKS = ("no", "approval", "fact", "must", "release")
HELD_FACTS = ("ci_workflow", "migrate_file", "flag_default")
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
         "> --when <ISO instant> --number D<n> [--reversibility '<line>']")


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


def status_lines(decide: str, ask: str, when: str, number: str, line: str | None) -> tuple[list[str], list[str]]:
    """(stdout lines, stderr lines) of the verb for these inputs."""
    if ask == "no":
        return [STANDING], ["provisional: nothing asked of a person"]
    if ask != "approval":
        return ([UNAVAILABLE + REASONS[ask], STANDING],
                [f"provisional: unavailable - {REASONS[ask]}, whatever decide says"])
    tier, facts = final_tier(line)
    held = held_fact(facts)
    if tier == "hard":
        why = "hard: " + ("no Reversibility line, so hard" if line is None else "the final tier is hard")
    elif held is not None:
        why = f"{held}=yes: {HELD_WHY[held]} (FR-033)"
    elif decide == "provisional":
        until = ratify_by(when)
        revert = f"- **Revert:** commits carrying Decision: {number}"
        return ([f"- **Status:** provisional · ratify by {until}", revert],
                [f"provisional: {tier}, no held fact; provisional until ratified by {until}"])
    else:
        return [UNAVAILABLE + APPROVAL, STANDING], [f"provisional: unavailable - decide is {decide}"]
    return [UNAVAILABLE + APPROVAL, STANDING], [f"provisional: unavailable - {why}"]


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


VERBS = {"status": status_verb}


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
