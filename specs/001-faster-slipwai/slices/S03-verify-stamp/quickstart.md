# Quickstart: S03-verify-stamp — what the demo follows

The actor is a developer in a project the factory generated. Everything below is run in that project.

1. Generate the Independent Test's project and make its first commit on a branch that is not the trunk:
   `slipwai generate stamped --backend python --frontend none` then, inside it, `git checkout -b topic`.
2. `make verify` — the full gate runs with the real toolchain and ends `verify: all gates passed`. If it adds a
   line saying the pass was not recorded (the first run installs things), run it once more.
3. `time make verify` — one line beginning `verify:` that says the gate did not run, when this tree passed, a
   short key and `VERIFY_FORCE=1`; no check runs. **SC-001: the wall time is under one second.** Write the
   command, the machine and the number here: *(the demo fills this in)*.
4. Change one character in a source file under `apps/service/src/`; `make verify` — every check runs. Undo it;
   `make verify` — every check runs again (the earlier stamp was removed), and the run after that is reused.
5. `make verify VERIFY_FORCE=1` — one line naming `VERIFY_FORCE`, then every check.
6. Add a comment to `scripts/check-imports.py`; `make verify` — every check runs.
7. `CI=true make verify` on a stamped tree — every check runs and nothing about a stamp is printed.
8. `git checkout main` (or the trunk's name) with the same files; `make verify` twice — both run every check.
9. `make ci` on a stamped tree — the gate's checks run.
10. Break a test; `make verify` fails; fix it back by `git checkout`; `make verify` runs every check (no stamp
    survived the failure).
11. `git status --short --ignored` — nothing of the stamp; `ls "$(git rev-parse --git-dir)/slipwai"` shows it.

Residual named for the cruise report: the Java backends carry the mechanism and no time claim (a JVM's start-up
is inside the budget on this machine by estimate only).
