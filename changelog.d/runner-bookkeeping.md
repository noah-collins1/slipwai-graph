MINOR

**A decision entry can now say which slices it binds, and a cruise run's briefs write and read that line.** The
entry `/cruise` writes gains a line directly after the Stage line, `- **Scope:** <slice ids, comma-separated> |
global`: the slices whose later decisions must agree with it, or `global` for a feature-level decision or one the
writer is unsure of. The cruise command, a newly seeded owner brief and the `drive-skipper` and `drive-bosun`
briefs now show and ask for it, and tell a delegate to read a slice's standing entries through
`python3 scripts/check-decisions.py --scope <slice-id>` (the whole log where no slice is named).

**Catch-up.** Nothing is asked of an existing log: an entry without the line is carried as global. A project's own
owner brief is never rewritten by a refresh; where it should show the new shape, add the `Scope:` line to its entry
example by hand.
