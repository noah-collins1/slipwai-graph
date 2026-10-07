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

# What `provisional` takes, as the verb decides it: the held-back facts are FR-033's three and the exclusion is D200's.
TAKES = ("where the change is easy or guarded to reverse and none of `flag_default=yes`, `ci_workflow=yes` or "
         "`migrate_file=yes` holds, and never for a gate, a check or CI question")

# The command's paragraph for the skipper protocol: who, how, and what an enforced one is not. Each `decide` value has
# its own sentence, and shadow and advisory take nothing: the rehearsal line is all they add.
COMMAND_PARAGRAPH = f"""\
**Provisional decisions.** Only the skipper takes an always-ask item provisionally, only a person's approval, and
only under one value of `decide`. It scores the tier first with `{_SCORE}`, then runs `{PROVISIONAL_VERB}` with
`--decide` the value in `.specify/cruise.json`, `--ask` the kind (`approval`, or `fact`, `must` or `release`),
`--when` the entry's `When`, `--number D<n>` and `--reversibility` the line `reversibility.py` printed, and without
it the verb reads the item as hard, so nothing is taken. It quotes the owner-brief line the item falls under. Under
`decide: provisional-shadow` an always-ask item is not taken: it stays `unavailable`, the skipper's `status` is
`unavailable`, and the entry only gains the `Provisional (shadow):` line saying what `provisional` would have done.
Under `decide: provisional-advisory` an always-ask item is not taken either: it stays `unavailable`, the skipper's
`status` is `unavailable`, and the entry only gains the `Provisional (advisory):` line, with the recommendation a
person can accept in one word. Under `decide: provisional`, and only there, the skipper takes an approval
provisionally {TAKES}, as `Status: provisional · ratify by <date>` with a `Revert:` line. Read the verb's output
line by line: the verb's first line, `unavailable: …`, is the skipper's `status: unavailable`, and its **Decision:**
says what a person must provide; `Status:` and `Revert:` the skipper writes where the entry shape puts them; the
`Provisional (shadow):` or `Provisional (advisory):` line goes after `Reversibility:`; the verb's other stderr lines
only say why, and go nowhere in the entry. Under advisory the skipper also returns the verb's stderr
`cruise: parked: …` line verbatim in `unresolved`, and a park on that item ends the run on that line.
Every other question is decided as under `recommended-first`. A question about a gate, a check or CI is never
provisional, whatever its declared facts; a credential, a third party's behaviour, a MUST or a release never is.
An enforced provisional decision, which only `decide: provisional` makes, is not a block: no bosun, no ⛔. Every
commit made under it carries the trailer `{TRAILER}`, which this session puts in every implement brief. A person's
`told: accept` is written as a `Decided by: human` entry taking the recommendation at `Status: standing`, and the
`unavailable` entry's `Status` becomes `overridden by D<m>`."""
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
# The dispatch sentence's addition: what the brief carries, and which items go to the delegate, under the provisional values.
DISPATCH_WORDS = (" (under `provisional-shadow`, `provisional-advisory` and `provisional` alike the brief also names "
                  "the `decide` value in `.specify/cruise.json`, and every always-ask item goes to the delegate even "
                  "where the stage recommends an answer)")
# Says what the "never decided" sentence of the command's *unavailable* paragraph excepts.
APPROVAL_EXCEPTION = ", except an approval under `decide: provisional` (*Provisional decisions*, above)"
NEVER_SETS = " The run never sets `decide`: `--set decide=…` refuses inside an iteration."
STOP_EXCEPTION = (
    "Under `decide: provisional` the skipper takes a person's approval provisionally " + TAKES + " (*Deciding*, "
    "below): that is not a block, so no bosun and no ⛔"
)
SETTINGS_WORDS = ('"take easy decisions provisionally" is `decide=provisional-shadow` first, then one rung at a '
                  "time")

# The skipper's brief says the same from its side.
SKIPPER_PARAGRAPH = f"""\
**Take an always-ask item provisionally only where the brief says `decide` allows it.** The brief names the
`decide` value, and only a person's approval that falls under a line of the owner brief's *Always ask a person* is
in question. Score its tier first with `{_SCORE}`, then run `{PROVISIONAL_VERB} --decide <value> --ask approval
--when <the entry's When> --number D<n> --reversibility '<the line it printed>'` and quote in **Why** the owner-brief
line the item falls under. Under `decide: provisional-shadow` an always-ask item is not taken: it stays
`unavailable`, your `status` is `unavailable`, and the entry only gains the `Provisional (shadow):` line saying what
`provisional` would have done. Under `decide: provisional-advisory` an always-ask item is not taken either: it stays
`unavailable`, your `status` is `unavailable`, and the entry only gains the `Provisional (advisory):` line. Under
`decide: provisional`, and only there, you take an approval provisionally {TAKES}, and your `status` is
`decided`. Read the verb's output line by line: the verb's first line, `unavailable: …`, is your `status:
unavailable`, and your **Decision:** says what a person must provide; `Status:` and `Revert:` you write where the
entry shape puts them; the `Provisional (shadow):` or `Provisional (advisory):` line goes after `Reversibility:`;
the verb's other stderr lines only say why, and go nowhere in the entry. Under `decide: provisional-advisory` the
verb's stderr line `cruise: parked: D<n> needs a person's approval; recommended: …` is returned verbatim in
`unresolved`. A question about a
gate, a check or CI is never provisional, whatever its declared facts; a credential, a third party's behaviour, a
MUST or a release never is (`--ask fact`, `must` or `release`). Every other question you decide as under
`recommended-first`. An enforced provisional decision, which only `decide: provisional` makes, is not a block, and
every commit made under it carries the trailer `{TRAILER}`."""

# The owner brief's two sentences.
OWNER_ALWAYS = ("Under `decide: provisional` an easy or guarded item here, unless it holds `flag_default=yes`, "
                "`ci_workflow=yes` or `migrate_file=yes` or is a gate, a check or CI question, may be taken "
                "provisionally and is listed for ratification (`commands/cruise.md` says how).")
OWNER_RECORD = ("A provisional entry's `Status` reads `provisional · ratify by <date>` and carries a `Revert:` line "
                "naming the commits to take back; the `Provisional (shadow)` and `Provisional (advisory)` lines say "
                "what a stricter mode would have done, and block nothing.")
