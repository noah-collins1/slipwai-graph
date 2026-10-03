# Data model — S23-refusal-in-subdirectory

No stored shape changes. One thing is said more exactly:

- **`.delivery-tools/written.json`** (under the project, ignored by git) — a JSON object, path → SHA-256 of what
  slipwai last left there, or `null` where it left the path absent. A **path** is spelled relative to the
  project's directory — where `project.json` is — with `/` separators, whether or not that directory is the top
  of its git repository. At the top this is what it always held; in a subdirectory project it held nothing
  before this slice.
- **An uncommitted change** — as `changed()` answers: a path under the project's directory that `git status`
  reports modified, added, deleted, renamed to, or untracked, spelled the same way. A change outside the
  project's directory is not one.
