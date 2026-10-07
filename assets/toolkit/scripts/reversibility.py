"""How hard a decision would be to take back: the rules, and the verb that scores declared facts (S26, FR-051).

`python3 scripts/reversibility.py --scope <value> [--written-to <value>] [--raise guarded|hard] <key>=<value>...`
prints the whole `- **Reversibility:** ...` line a decision entry carries, and on stderr one line naming the rules
that fired. The facts are a closed list; the tier is the highest any rule gives; a missing or unaccepted fact scores
`hard`. `RULES` keeps every version of the table this file has shipped: a line names the version that scored it, and
a shipped version is only ever added to, never edited (a new version is a decision taken at the hard tier).
The gate (`check-decisions.py`) loads this file by path, only for a log that carries a `Reversibility:` or
`Proposed rule:` line, and `check_log()` holds each line to the grammar and to the tier its named version derives.
The scope is read by `scope_tokens`, a copy of the gate's own reading, so the verb works with nothing beside it; a
caller that holds the gate's function passes it to `score()` instead. Nothing here prints or exits outside `main`.
"""
from __future__ import annotations

import json
import posixpath
import re
import sys
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path

LABEL = "- **Reversibility:** "
ARROW = " → "
TIERS = ("easy", "guarded", "hard")
YES_NO = ("yes", "no")
# Version 1's closed list, in the order the line writes it, each with the values it accepts. `FACT_LISTS` keeps each
# rules version's own list: a version that adds a fact adds a list, and a line is read against the list it names.
FACTS: dict[str, tuple[str, ...]] = {
    "contract": YES_NO, "schema": YES_NO, "auth": YES_NO, "customer_visible": YES_NO, "export": YES_NO,
    "ci_workflow": YES_NO, "migrate_file": YES_NO, "behind_flag": ("yes", "no", "no-code"),
    "flag_default": YES_NO, "rollback_complexity": ("trivial", "hours", "days", "needs-migration"),
}
HARD_FACTS = tuple(list(FACTS)[:7])
USAGE = ("usage: reversibility.py --scope <value> [--written-to <value>] [--raise guarded|hard] <key>=<value>...")

SLICE_ID = re.compile(r"[A-Za-z]+[0-9]+(?![A-Za-z0-9_])(?:[.-][A-Za-z0-9._-]*[A-Za-z0-9])?")
HEAD = re.compile(r"([A-Za-z]+)([0-9]+)")


def one_id(token: str) -> bool:
    """False for a token carrying a second id head after its first (`S01-S03`): the gate's own test."""
    first = HEAD.match(token)
    assert first is not None
    for piece in re.split(r"[.-]", token)[1:]:
        later = HEAD.fullmatch(piece)
        if later and later.group(1).lower() == first.group(1).lower():
            return False
    return True


def scope_tokens(value: str) -> list[str] | None:
    """The slice ids a `Scope:` value lists, `["global"]` for the word alone, or None where it is neither."""
    tokens = [part.strip().strip("`").strip() for part in value.split(",")]
    if tokens == ["global"]:
        return tokens
    if value.strip() and all(SLICE_ID.fullmatch(token) and one_id(token) for token in tokens):
        return tokens
    return None


def dependants(scope: str, reader: Callable[[str], list[str] | None] = scope_tokens) -> str:
    """`one`, `several` or `global`: what a scope says about who is bound by the decision (unreadable is global)."""
    tokens = reader(scope)
    if tokens is None or tokens == ["global"]:
        return "global"
    return "one" if len(tokens) == 1 else "several"


def rules_v1(facts: dict[str, str], bound: str) -> tuple[str, list[str]]:
    """Rules version 1: the facts and the dependants class give the tier and the rules that fired."""
    fired: list[tuple[str, str]] = []
    for number, key in enumerate(HARD_FACTS, 1):
        if facts.get(key) == "yes":
            fired.append((f"H{number} {key}=yes", "hard"))
    rollback = facts.get("rollback_complexity")
    if rollback in ("days", "needs-migration"):
        fired.append((f"R1 rollback_complexity={rollback}", "hard"))
    if rollback == "hours":
        fired.append(("R2 rollback_complexity=hours", "guarded"))
    if facts.get("behind_flag") == "no":
        fired.append(("F1 behind_flag=no", "guarded"))
    if facts.get("flag_default") == "yes":
        fired.append(("F2 flag_default=yes", "guarded"))
    if bound == "several":
        fired.append(("D1 scope names several slices", "guarded"))
    if bound == "global":
        fired.append(("D2 scope is global or unreadable", "hard"))
    for key, accepted in FACTS.items():
        if facts.get(key, "missing") not in accepted:
            fired.append((f"U1 {key}={facts.get(key, 'missing')}", "hard"))
    tier = max((t for _, t in fired), key=TIERS.index, default="easy")
    return tier, [name for name, _ in fired]


# Every version this file has shipped. Never edit one; add the next, with its fact list below.
RULES: dict[int, Callable[[dict[str, str], str], tuple[str, list[str]]]] = {1: rules_v1}
FACT_LISTS: dict[int, dict[str, tuple[str, ...]]] = {1: FACTS}
CURRENT = max(RULES)


def steps(tier: str, raise_to: str | None) -> list[str]:
    """The tiers a line writes: the computed one, then each one-tier step up to `raise_to`; ValueError to lower."""
    if raise_to is None:
        return [tier]
    if TIERS.index(raise_to) < TIERS.index(tier):
        raise ValueError(f"--raise {raise_to} would lower the computed tier {tier}; a tier is never lowered")
    return list(TIERS[TIERS.index(tier):TIERS.index(raise_to) + 1])


def project_root(script: Path, depth: int) -> Path:
    """The project root as `check-decisions.py` finds it: the nearest parent holding `project.json`."""
    for candidate in script.parents:
        if (candidate / "project.json").is_file():
            return candidate
    return script.parents[depth]


def written_paths(value: str) -> list[str]:
    """The paths a `Written to` value names, as `check-decisions.py`'s `paths_of` reads them: backticked, else
    comma-separated."""
    quoted = re.findall(r"`([^`]+)`", value)
    if quoted:
        return quoted
    return [part.strip() for part in value.split(",") if part.strip()]


def on_list(written: Iterable[str], listed: set[str]) -> bool:
    """Whether any `Written to` path is on the committed list, read as a path: `./` and backslashes are resolved, and a
    directory (with or without its trailing `/`) matches when a listed file is under it. The verb and the gate share it."""
    def clean(path: str) -> str:
        return posixpath.normpath(path.strip().replace("\\", "/"))
    files = {clean(entry) for entry in listed}
    for path in map(clean, filter(str.strip, written)):
        if path in files or path == "." or any(entry.startswith(path + "/") for entry in files):
            return True
    return False


def propagated(root: Path) -> set[str] | None:
    """The paths `migrate` propagates, from the committed list, or None where the project has no list.

    `<layout.delivery>/.written` where `project.json` says `origin` is `adopted` (`.written` at the root where the
    delivery directory is `.`), else `.slipwai/propagated`; one project-relative path per line. A list that cannot be
    read as UTF-8 text is no list: it fails closed, as a missing one does."""
    try:
        document = json.loads((root / "project.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        document = {}
    document = document if isinstance(document, dict) else {}
    if document.get("origin") == "adopted":
        layout = document.get("layout")
        delivery = layout.get("delivery", ".") if isinstance(layout, dict) else "."
        home = root / str(delivery) / ".written"
    else:
        home = root / ".slipwai" / "propagated"
    try:
        lines = home.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    return {line.strip() for line in lines if line.strip()}


def with_list(facts: dict[str, str], written: list[str] | None, listed: set[str] | None) -> dict[str, str]:
    """`facts` with `migrate_file` as the committed list says: raised to yes by a listed path, never lowered; `no-list`
    wherever the project has no list, since nothing then says what `migrate` propagates."""
    if facts.get("migrate_file") != "no":
        return facts
    if listed is None:
        return {**facts, "migrate_file": "no-list"}
    return {**facts, "migrate_file": "yes"} if on_list(written or [], listed) else facts


def score(facts: dict[str, str], scope: str, raise_to: str | None = None, version: int = CURRENT,
          reader: Callable[[str], list[str] | None] = scope_tokens, written: list[str] | None = None,
          listed: set[str] | None = None) -> tuple[str, list[str]]:
    """The whole `Reversibility:` line and the rules that fired, for declared facts and the entry's `Scope:` value.

    `written` (the paths of `Written to`) with `listed` (the committed list) raise `migrate_file`; see `with_list`."""
    facts = with_list(facts, written, listed)
    tier, fired = RULES[version](facts, dependants(scope, reader))
    written = " ".join(f"{key}={facts.get(key, 'missing')}" for key in FACT_LISTS[version])
    return f"{LABEL}{ARROW.join(steps(tier, raise_to))} · rules {version} · {written}", fired


def parse_line(value: str) -> tuple[list[str], int, dict[str, str]]:
    """(tiers, rules version, facts) from the text after the label; ValueError names the field or the key at fault."""
    parts = value.split(" · ")
    if len(parts) != 3:
        raise ValueError("is not `<tiers> · rules <n> · <fact>=<value> ...`")
    tiers = [word.strip() for word in re.split(r"→|->", parts[0])]
    for word in tiers:
        if word not in TIERS:
            raise ValueError(f"names {word!r}, which is not a tier (easy, guarded or hard)")
    for before, after in zip(tiers, tiers[1:], strict=False):
        gap = TIERS.index(after) - TIERS.index(before)
        if gap != 1:
            raise ValueError(f"has a step {before} → {after} that " + (
                "lowers a tier" if gap < 0 else "repeats a tier" if gap == 0 else "skips a tier"))
    named = re.fullmatch(r"rules ([0-9]+)", parts[1].strip())
    if named is None:
        raise ValueError(f"names {parts[1].strip()!r}, not `rules <n>`")
    version = int(named.group(1))
    if version not in RULES:
        raise ValueError(f"names rules {named.group(1)}, which this gate does not know "
                         f"(it knows {', '.join(map(str, RULES))})")
    facts: dict[str, str] = {}
    for token in parts[2].split():
        key, separator, given = token.partition("=")
        if not separator or not key or not given:
            raise ValueError(f"has {token!r}, which is not key=value")
        if key not in FACT_LISTS[version]:
            raise ValueError(f"has the key `{key}`, which is not a fact of rules {version} "
                             f"(the facts are {', '.join(FACT_LISTS[version])})")
        if key in facts:
            raise ValueError(f"has the key `{key}` twice")
        facts[key] = given
    return tiers, version, facts


def line_findings(where: str, fields: Mapping[str, str], twice: set[str], reader: Callable[[str], list[str] | None],
                  listed: set[str] | None) -> list[str]:
    """The findings for one entry's `Reversibility:` line (none where it has none); `where` is `<file>:<line>: D<n>`."""
    if "Reversibility" not in fields:
        return []
    found = []
    if "Reversibility" in twice:
        found.append(f"{where} has more than one `Reversibility:` line; an entry says it once")
    try:
        tiers, version, facts = parse_line(fields["Reversibility"])
    except ValueError as error:
        return found + [f"{where} `Reversibility` {error}"]
    if facts.get("migrate_file") == "no":
        if listed is None:
            found.append(f"{where} `Reversibility` says migrate_file=no, but this project has no committed list of "
                         "migrate-propagated files, so nothing says it is no")
        elif on_list(written_paths(fields.get("Written to", "")), listed):
            found.append(f"{where} `Reversibility` says migrate_file=no, but a `Written to` path is on the "
                         "committed list")
    derived, fired = RULES[version](facts, dependants(fields.get("Scope", ""), reader))
    if tiers[0] != derived:
        found.append(f"{where} `Reversibility` starts at {tiers[0]}, but rules {version} derive {derived} from its "
                     f"facts ({'; '.join(fired) or 'no rule fired'})")
    return found


def rule_findings(where: str, number: int, value: str, known: set[int]) -> list[str]:
    """The findings for one entry's `Proposed rule:` value: two distinct cited ids other than its own, each an entry of
    the log (its `Status` is not read, D185). The ids counted are those in the parenthesis `(same shape as D<a>, D<b>)`,
    wherever it stands in the value and with any text after it, so a `D<n>` the sentence itself mentions is not one."""
    inside = re.findall(r"\(\s*same shape as([^()]*)\)", value, re.I)
    cited = {int(n) for n in re.findall(r"\bD([0-9]+)\b", " ".join(inside))}
    found = [f"{where} `Proposed rule` cites D{n}, which is no entry of this log" for n in sorted(cited - known)]
    if len(cited - {number}) < 2:
        found.append(f"{where} `Proposed rule` cites fewer than two entries other than its own "
                     "(`(same shape as D<a>, D<b>)`)")
    return found


def check_log(relative: str, items: Iterable[tuple[int, int | None, Mapping[str, str], set[str]]],
              reader: Callable[[str], list[str] | None], listed: set[str] | None,
              verb: str = "python3 scripts/reversibility.py") -> tuple[list[str], list[str]]:
    """(findings, notes) for one decisions log: `items` are (line, entry number or None, fields, repeated labels) as the
    gate parsed them, `reader` the gate's own `scope_tokens`, `listed` the committed list, `verb` how this project
    runs this file. The second loop is the missing-line note."""
    findings: list[str] = []
    notes: list[str] = []
    entries = [item for item in items if item[1] is not None]
    known = {number for _, number, _, _ in entries if number is not None}
    for line, number, fields, twice in entries:
        findings += line_findings(f"{relative}:{line}: D{number}", fields, twice, reader, listed)
        if number is not None and "Proposed rule" in fields:
            findings += rule_findings(f"{relative}:{line}: D{number}", number, fields["Proposed rule"], known)
    seen = False  # file order, as `scope_notes` reads it: the first entry with the line starts it
    for line, number, fields, _ in entries:
        if "Reversibility" in fields:
            seen = True
        elif seen:
            notes.append(f"check-decisions: note: {relative}:{line}: D{number} has no `Reversibility:` line after an "
                         f"entry that has one; score it with {verb}")
    return findings, notes


def parse_arguments(arguments: list[str]) -> tuple[dict[str, str], dict[str, str]]:
    """(options, facts) from the command line; ValueError names what is wrong."""
    options: dict[str, str] = {}
    facts: dict[str, str] = {}
    rest = iter(arguments)
    for argument in rest:
        if argument in ("--scope", "--written-to", "--raise"):
            value = next(rest, None)
            if value is None or argument in options:
                raise ValueError(f"{argument} needs one value, once")
            options[argument] = value
            continue
        key, separator, value = argument.partition("=")
        if not separator or not key or not value:
            raise ValueError(f"{argument!r} is not key=value")
        if key not in FACT_LISTS[CURRENT]:
            raise ValueError(f"{key!r} is not a fact (the facts are {', '.join(FACT_LISTS[CURRENT])})")
        if key in facts:
            raise ValueError(f"{key!r} is given twice")
        stray = [word for word in (*TIERS, "→", "->", "·") if word in value]
        if stray:
            raise ValueError(f"{key}={value!r} contains {stray[0]!r}; no fact value holds a tier word, an arrow or ·")
        if any(character.isspace() for character in value):
            raise ValueError(f"{key}={value!r} contains whitespace, where the line's facts are divided")
        facts[key] = value
    if "--scope" not in options:
        raise ValueError("--scope is required")
    if options.get("--raise", "guarded") not in TIERS[1:]:
        raise ValueError(f"--raise takes guarded or hard, not {options['--raise']!r}")
    return options, facts


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")  # the line carries `→` and `·`; a pipe may not
    arguments = sys.argv[1:]
    if arguments == ["--help"]:
        print(USAGE)
        return 0
    try:
        options, facts = parse_arguments(arguments)
        written = options.get("--written-to")
        line, fired = score(facts, options["--scope"], options.get("--raise"),
                            written=None if written is None else written_paths(written),
                            listed=propagated(project_root(Path(__file__).resolve(), 1)))
    except ValueError as error:
        print(f"reversibility: {error}\n{USAGE}".replace("\n", " — ", 1), file=sys.stderr)
        return 2
    print(line)
    print("reversibility: " + ("; ".join(fired) if fired else "no rule fired"), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
