# Quickstart: S03-verify-stamp — what the demo follows

The actor is a developer in a project the factory generated. Everything below is run in that project.

1. Generate the Independent Test's project in a scratch directory and move to a branch that is not the trunk:
   `slipwai generate stamped --backend python --frontend none --output <scratch>` (it makes the first commit on
   `main` itself), then, inside the project, `git checkout -b topic`.
2. `make verify`, twice. The first run has no environment yet, so before its first check it prints `verify: the
   full gate runs and this run records nothing — …` and names what it could not read; it may also end with a line
   saying the pass was not recorded, because a check wrote a file. Run it until a run ends `verify: all gates
   passed` with no such line: that run recorded.
3. `time make verify` — one line beginning `verify:` that says the gate did not run, when this tree passed, a
   short key and `VERIFY_FORCE=1`; no check runs. **SC-001: the wall time is under one second.** Write the
   command, the machine and the number here: measured at the second demo of 2026-10-04 (cruise iteration 11,
   AC-S03-42, code at c1a626b) with `time make verify`, the whole command, `real`, on a 12th Gen Intel Core
   i5-12400 (12 cores), Linux 7.0.0-31 x86_64, GNU Make 4.4.1, git 2.53.0, uv 0.12.20, Python 3.14.4, Node
   v22.22.1, npm 9.2.0 — ten runs in a row at step 15:
   **0.537 s, 0.546 s, 0.549 s, 0.550 s, 0.550 s, 0.550 s, 0.544 s, 0.547 s, 0.543 s, 0.544 s** (worst 0.550 s;
   twenty-two more through the demo, 0.535 s to 0.565 s), against 3.8 s for the full gate on the same tree.
4. Change one character in a source file under `apps/service/src/` (a change the formatter accepts — a word
   inside a docstring; whether that run passes is not the point, that every check runs is). Undo it;
   `make verify` — every check runs again (the earlier stamp was removed), and the run after that is reused.
5. `make verify VERIFY_FORCE=1` — one line naming `VERIFY_FORCE`, then every check.
6. Add a comment to `scripts/check-imports.py`; `make verify` — every check runs.
7. `CI=true make verify` on a stamped tree — every check runs and nothing about a stamp is printed.
8. `git checkout main` (or the trunk's name) with the same files; `make verify` twice — both run every check.
9. `make ci` on a stamped tree — every check of the gate runs, no line about a stamp is printed, and the stamp
   file is the same bytes afterwards (D83: `ci` runs the checks through their own target and records nothing).
   `make ci` goes on to the audit and the integration tests, which need more than this machine may have: its
   exit code is not the evidence.
10. Break a test; `make verify` fails; fix it back by `git checkout`; `make verify` runs every check (no stamp
    survived the failure).
11. `git status --short --ignored` — nothing of the stamp; `ls "$(git rev-parse --git-dir)/slipwai"` shows it.

Residual named for the cruise report: the Java backends carry the mechanism and no time claim (a JVM's start-up
is inside the budget on this machine by estimate only).

Added after the adversary pass (D83), for the second demo:

12. With `scratch_*.py` added to `.gitignore` and committed, and the gate stamped again: write a file
    `apps/service/tests/scratch_try.py` that does not compile — `git status --short` shows nothing, and `make
    verify` runs every check and fails. Remove the file and run until the gate records again.
13. Start `make verify VERIFY_FORCE=1` and, while its checks run, start a second `make verify VERIFY_FORCE=1` in
    another shell: the run that started first ends `verify: this pass was not recorded — another run of the gate
    started here after this one began, so only that run may record`.
14. `git init` a copy of the project with no commit yet and run `make verify` twice: both run every check and say
    nothing of a stamp.
15. Step 3 again, seven times: the measurement that replaces the first one (AC-S03-42).

