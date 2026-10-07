"""The three records `/cruise` writes in a fixed shape: a decision, a demo, and the checkpoint a compacted context resumes from.

Their shapes live here, apart from the command that shows them and the brief that repeats them, because
three things are written from them — `commands/cruise.md`, the owner brief, and the `check-decisions` gate's
expectations — and a shape stated once cannot drift between them. The checkpoint is the newest: a context can
be summarised by the harness at any point, and what a summary loses is the state nothing on disk carries —
which delegates are out, a question half-answered, which slice's demo comes next — so the command keeps that
in one small file and re-reads it, and the harnesses that can run a command after compaction replay it.
"""
from __future__ import annotations

from .cruise_agents import BOSUN, BROWSER, HAND, SCORE_VERB, SKIPPER
from .cruise_provisional import MODE_LINE, REVERT_LINE, STATUS_FORMS

CHECKPOINT = "specs/cruise-checkpoint.md"
STOP_FILE = ".specify/cruise.stop"
# The runner's pid while it runs, where a detached runner writes what a foreground one prints, and the last
# message a harness's after-response hook kept for a stop hook whose event does not carry it.
RUNNER_PID = ".specify/cruise.pid"
RUNNER_LOG = ".specify/cruise-run.log"
# The harness's raw event stream the feed in the run log was rendered from, and how far the watch seat has read.
RUNNER_STREAM = ".specify/cruise-stream.jsonl"
WATCH_CURSOR = ".specify/cruise-watch.cursor"
# Where `/cruise` is configured, and the runner every seat command speaks to; `cruise.py` re-exports both.
CONFIG = ".specify/cruise.json"
SCRIPT = "scripts/agents/cruise.py"
LAST_RESPONSE = ".specify/cruise-last-response.txt"
# What a person queued for the run through `tell`, until an iteration takes it; and what an iteration was given,
# until the runner writes it into that iteration's log entry.
INBOX = ".specify/cruise-inbox.jsonl"
TOLD = ".specify/cruise-told.jsonl"
# The rule that makes a decision entry also an ADR, stated once for the command and read by its tests. `{REPORT}`
# is `cruise_stops.REPORT`, which the command substitutes.
ADR_RULE = """\
**A decision that outlives its slice is also an ADR.** Ask the `architecture-decisions` skill's one question
of every entry, host-decided or skipper-decided: would reversing it cost a migration rather than a refactor —
an event's schema or name, stream identity, tenancy, the store, personal data, identity, a new dependency, a
published contract? Where it would, write `docs/adr/NNNN-<title>.md` in Nygard's five sections at `Proposed` —
the run never accepts its own architecture decision — with the next unused number, allocated here the way
`D<n>` is, and name it in the entry's `Written to` beside the artifact. The entry is the log of what was
decided; the ADR is where the next slice looks for why, and `{REPORT}` lists every ADR still `Proposed`."""
# The line a decision's reversibility is written on, and what the session does about it (D174, D177, D178).
REVERSIBILITY_RULE = f"""\
**Every entry says how hard it is to reverse.** This session runs `{SCORE_VERB}` for every entry it writes,
host-decided or skipper-decided, with that entry's facts, `Scope:` and `Written to`, and writes the line the verb
prints after `Confidence`. The flags are `--scope`, `--written-to` and, to escalate a tier, `--raise`; quote each
value, as in `--scope 'S1, S2' --written-to 'a.md, b.md' contract=no`, and never paste backticks inside double
quotes. It also adds the feature's entry headings — each `D<n>` with its heading, Stage and
Scope, out-of-scope entries included — to every skipper brief, so the skipper can count what it has decided
alike. `Proposed rule:` is the skipper's alone, and only where the count is three."""
DECISION_ENTRY = f"""## D<n> — <the question, in one line>
- **Stage:** <stage> · **Slice:** <id> · **When:** <ISO instant> · **Iteration:** <n>
- **Scope:** <slice ids, comma-separated> | global — a feature-level or doubtful decision is `global`
- **Question:** <as the stage raised it>
- **Options:** <each, marking the one the stage recommended>
- **Decision:** <one>
- **Why:** <in the actor's terms>
- **Decided by:** host (stage recommendation) | host (standing decision D<m>) | {SKIPPER} (<model>) | {BOSUN} | human
- **Confidence:** high | medium | low · **Would reverse if:** <the one condition>
- **Reversibility:** <tier> · rules <n> · <facts, as {SCORE_VERB} prints the line>
- **Proposed rule:** <optional: one owner-brief sentence, where three entries share a reason> (same shape as D<a>, D<b>)
{MODE_LINE}
- **Written to:** <the artifact paths the answer went into>
- **Status:** standing | overridden by D<m> | overridden by human <date> | {STATUS_FORMS}
{REVERT_LINE}"""
ENTRY_RULES = f"{REVERSIBILITY_RULE}\n\n{ADR_RULE}"
DEMO_ENTRY = f"""## <ISO instant> — <accepted | behaviour | implementation> · iteration <n> · {HAND} (<model>)
- **Started with:** <the literal command or URL> · **Seeded:** <what, or none>
- **Driven through:** {BROWSER} | <harness browser tool> | HTTP | CLI — <why, where not the first>
- **Examples:** <one line each — R1 e1: passed · R2 e1: failed, expected X, saw Y · R3 e2: unreachable, why>
- **Evidence:** <paths under demo/>
- **Feedback:** <what re-entered the ladder and at which stage, or the note for the next slice>"""
CHECKPOINT_ENTRY = f"""# Cruise checkpoint — iteration <n>
- **Feature:** <feature> · **Slice:** <id> · **Stage:** <stage> · **Written:** <ISO instant>
- **Delegates out:** <type · manifest · what it was asked>, one per line, or none
- **Open question:** <the question and the stage that raised it, or none>
- **Next:** <the one next step, in the ladder's words>
- **Rules:** run commands/drive.md as written; decide at its stops by the stop table; decisions to
  decisions.md; demos to demo-log.md; end with one of the four last lines; `{STOP_FILE}` stops the run"""
