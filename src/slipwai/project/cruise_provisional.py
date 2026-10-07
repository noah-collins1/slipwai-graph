"""What `/cruise` says about provisional decisions (S27), kept out of `cruise.py` so that file stays within its cap.

One constant per sentence or list, imported by the writers of the settings table and the command; the toolkit's
`scripts/agents/cruise.py` cannot import from here, so a test holds its copy to these.
"""
from __future__ import annotations

DECIDE_VALUES: tuple[str, ...] = (
    "recommended-first", "skipper-always", "provisional-shadow", "provisional-advisory", "provisional",
)
DECIDE_CONTROLS = (
    "who answers a product question: the host where the stage recommends an answer or a standing decision covers "
    "it and `drive-skipper` otherwise, or `drive-skipper` for every question. Change it to `provisional-shadow` "
    "when always-ask questions are stalling slices and you want to see which ones would have been taken "
    "provisionally before letting any be; move on to `provisional-advisory`, then `provisional`, once the shadow "
    "lines read right."
)

# The three verbs a run speaks to (S27); their output is the toolkit's, and the briefs name them where they use them.
PROVISIONAL_VERB = "python3 scripts/provisional.py status"
AUDIT_VERB = "python3 scripts/provisional.py audit"
MODE_VERB = "python3 scripts/agents/cruise.py mode"
_SCORE = "python3 scripts/reversibility.py"
# The trailer every commit made under a provisional decision carries, so one `git log --grep` finds them all.
TRAILER = "Decision: D<n>"
# The three new `Status` forms, the `Revert:` line after `Status`, and the mode line after `Reversibility:`.
STATUS_FORMS = "provisional · ratify by <date> | ratified <date> | reverted <date>"
REVERT_LINE = ("- **Revert:** <on a provisional, ratified or reverted entry: commits carrying Decision: D<n>, "
               "its own number>")
MODE_LINE = ("- **Provisional (shadow | advisory):** <optional: final tier> · <provisional · ratify by <date> | "
             "blocks (hard) | blocks (<fact>=yes)> · Revert: commits carrying Decision: D<n>")

# The command's paragraph for the skipper protocol: who, how, and what an enforced one is not.
COMMAND_PARAGRAPH = f"""\
**Provisional decisions.** Under `decide: provisional-shadow`, `provisional-advisory` or `provisional`, only the
skipper takes an always-ask item provisionally, and only a person's approval: it scores the tier first with
`{_SCORE}`, then runs `{PROVISIONAL_VERB}` with `--decide` the value in `.specify/cruise.json`, `--ask` the
kind (`approval`, or `fact`, `must` or `release`), `--when` the entry's `When` and `--number D<n>`, writes the lines
the verb prints where the entry shape puts them, and quotes the owner-brief line the item falls under. Every other
question is decided as under `recommended-first`. A question about a gate, a check or CI is never provisional,
whatever its declared facts; a credential, a third party's behaviour, a MUST or a release never is. An enforced
provisional decision is not a block: no bosun, no ⛔ on the board, the skipper's `status` stays `decided`. Every
commit made under it carries the trailer `{TRAILER}`, which this session puts in every implement brief. Under
advisory the park line is the one the verb prints; a person's `told: accept` is written as a `Decided by: human`
entry taking the recommendation at `Status: standing`, and the `unavailable` entry's `Status` becomes
`overridden by D<m>`."""
MODE_SENTENCE = (
    f"In an iteration, run `{MODE_VERB}` too (with `--feature <name>` where the run has one): append the entry it "
    f"prints, scored with `{_SCORE}` like every entry, and end on its `cruise: parked:` line where it prints one."
)
AUDIT_SENTENCE = (
    f"Before `cruise: done`, run `{AUDIT_VERB}` (with `--feature <name>` where the run has one) and end on the "
    "`cruise: parked: ratify D<n>` line where it prints one: a person ratifies by editing that entry's `Status` to "
    "`ratified <date>`, or reverts the commits carrying its trailer and writes `reverted <date>`, since the run "
    "does neither."
)
NEVER_SETS = " The run never sets `decide`: `--set decide=…` refuses inside an iteration."
STOP_EXCEPTION = (
    "Under `decide: provisional` the skipper takes a person's approval provisionally where the change is easy or "
    "guarded to reverse (*Deciding*, below): that is not a block, so no bosun and no ⛔"
)
SETTINGS_WORDS = ('"take easy decisions provisionally" is `decide=provisional-shadow` first, then one rung at a '
                  "time")

# The skipper's brief says the same from its side.
SKIPPER_PARAGRAPH = f"""\
**Take an always-ask item provisionally only where the brief says `decide` allows it.** The brief names the
`decide` value. Under `provisional-shadow`, `provisional-advisory` or `provisional`, a person's approval that falls
under a line of the owner brief's *Always ask a person* is yours alone to take provisionally, and only after you have
scored its tier with `{_SCORE}`: then run `{PROVISIONAL_VERB} --decide <value> --ask approval --when <the entry's
When> --number D<n> --reversibility '<the line it printed>'` and write the lines it prints, where the entry shape
puts them — `Status:` and `Revert:`, or the mode line after `Reversibility:` — quoting in **Why** the owner-brief line
the item falls under. A question about a gate, a check or CI is never provisional, whatever its declared facts; a
credential, a third party's behaviour, a MUST or a release never is (`--ask fact`, `must` or `release`). Every other
question you decide as under `recommended-first`. An enforced provisional decision is not a block: your `status` is
`decided`, and every commit made under it carries the trailer `{TRAILER}`."""

# The owner brief's two sentences.
OWNER_ALWAYS = ("Under `decide: provisional` an easy or guarded item here may be taken provisionally and is listed "
                "for ratification (`commands/cruise.md` says how).")
OWNER_RECORD = ("A provisional entry's `Status` reads `provisional · ratify by <date>` and carries a `Revert:` line "
                "naming the commits to take back; the `Provisional (shadow)` and `Provisional (advisory)` lines say "
                "what a stricter mode would have done, and block nothing.")
