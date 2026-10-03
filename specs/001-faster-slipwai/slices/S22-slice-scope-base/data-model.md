# Data model — S22-slice-scope-base

No stored data. What the checker reads to choose a base, and the derived notions this slice adds:

| Thing | Where | Read as |
|---|---|---|
| Recorded trunk name | working tree `project.json` `ci.branch` | a **usable name** or nothing; never read from the base (it is what finds the base) |
| **Usable name** | derived (D30) | a string, `refs/heads/` stripped, a valid branch name, not `slice/<id>`, not starting `-` or `refs/` |
| Trunk refs | `refs/heads/<name>`, `refs/remotes/origin/<name>` | by full name only; a tag never answers |
| **Trunk** | derived (D30) | recorded name where usable and a ref exists, else `main`, else `master`, else none |
| Pull-request target | `GITHUB_BASE_REF`, `CI_MERGE_REQUEST_TARGET_BRANCH_NAME` | a second candidate where usable and a ref exists |
| **Base** | derived | newest within one name; oldest across trunk and target |
| **Forge checkout** | derived (D31) | the branch's name came from `GITHUB_HEAD_REF` / `CI_COMMIT_REF_NAME` and `HEAD` is detached |
| Ownership record | `project.json` at the base | unchanged (T017) |

No state transitions.
