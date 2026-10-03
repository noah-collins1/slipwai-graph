# Data model — S20-slice-scope-root

No stored data. What the checkers read, and the two derived notions this slice adds:

| Thing | Where | Read as |
|---|---|---|
| Deployable path | `project.json` `deployables.<name>.path` | stripped of `/`; `.` is the **root deployable**, the fallback owner; empty or missing owns nothing |
| Delivery directory | the checker's own location (`DELIVERY`) | the host's, except `survey/pinned.md` and `survey/running.md` |
| Factory-written list | `<delivery>/.written`, one path per line, optional | each line is the host's; absence is not an error |
| CI gate | `project.json` `ci.gate`, when a string | the host's |
| **Host surface** | derived (D18) | fixed names ∪ delivery directory ∪ `.written` ∪ `ci.gate`; consulted only where the root deployable would own the path |
| Register id | first cell of a row in `specs/<feature>/slices/README.md` | whole: `[A-Za-z]+\d+[A-Za-z0-9._-]*` |
| **Bare prefix** | derived (D19) | `[A-Za-z]+\d+` of the id; accepted as an adversary-row heading and as a record directory where the whole id finds nothing |

No state transitions.
