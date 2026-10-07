"""How hard a decision would be to take back: the rules, and the verb that scores declared facts (S26, FR-051).

`python3 scripts/reversibility.py --scope <value> [--written-to <value>] [--raise guarded|hard] <key>=<value>...`
prints the whole `- **Reversibility:** ...` line a decision entry carries, and on stderr one line naming the rules
that fired. The facts are a closed list; the tier is the highest any rule gives; a missing or unaccepted fact scores
`hard`. `RULES` keeps every version of the table this file has shipped: a line names the version that scored it, and
a shipped version is only ever added to, never edited (a new version is a decision taken at the hard tier).
The gate (`check-decisions.py`) loads this file by path to re-derive a line's first tier. The scope is read by
`scope_tokens`, a copy of the gate's own reading, so the verb works with nothing beside it; a caller that holds the
gate's function passes it to `score()` instead. Nothing here prints or exits outside `main`.
"""
from __future__ import annotations

import re
import sys
from collections.abc import Callable

LABEL = "- **Reversibility:** "
ARROW = " → "
TIERS = ("easy", "guarded", "hard")
YES_NO = ("yes", "no")
# The closed list, in the order the line writes it, each with the values it accepts.
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


# Every version this file has shipped. Never edit one; add the next.
RULES: dict[int, Callable[[dict[str, str], str], tuple[str, list[str]]]] = {1: rules_v1}
CURRENT = max(RULES)


def steps(tier: str, raise_to: str | None) -> list[str]:
    """The tiers a line writes: the computed one, then each one-tier step up to `raise_to`; ValueError to lower."""
    if raise_to is None:
        return [tier]
    if TIERS.index(raise_to) < TIERS.index(tier):
        raise ValueError(f"--raise {raise_to} would lower the computed tier {tier}; a tier is never lowered")
    return list(TIERS[TIERS.index(tier):TIERS.index(raise_to) + 1])


def score(facts: dict[str, str], scope: str, raise_to: str | None = None, version: int = CURRENT,
          reader: Callable[[str], list[str] | None] = scope_tokens) -> tuple[str, list[str]]:
    """The whole `Reversibility:` line and the rules that fired, for declared facts and the entry's `Scope:` value."""
    tier, fired = RULES[version](facts, dependants(scope, reader))
    written = " ".join(f"{key}={facts.get(key, 'missing')}" for key in FACTS)
    return f"{LABEL}{ARROW.join(steps(tier, raise_to))} · rules {version} · {written}", fired


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
        if key not in FACTS:
            raise ValueError(f"{key!r} is not a fact (the facts are {', '.join(FACTS)})")
        if key in facts:
            raise ValueError(f"{key!r} is given twice")
        facts[key] = value
    if "--scope" not in options:
        raise ValueError("--scope is required")
    if options.get("--raise", "guarded") not in TIERS[1:]:
        raise ValueError(f"--raise takes guarded or hard, not {options['--raise']!r}")
    return options, facts


def main() -> int:
    arguments = sys.argv[1:]
    if arguments == ["--help"]:
        print(USAGE)
        return 0
    try:
        options, facts = parse_arguments(arguments)
        line, fired = score(facts, options["--scope"], options.get("--raise"))
    except ValueError as error:
        print(f"reversibility: {error}\n{USAGE}".replace("\n", " — ", 1), file=sys.stderr)
        return 2
    print(line)
    print("reversibility: " + ("; ".join(fired) if fired else "no rule fired"), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
