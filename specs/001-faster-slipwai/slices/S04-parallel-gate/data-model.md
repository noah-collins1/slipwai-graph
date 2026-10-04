# Data Model: S04-parallel-gate

No stored entity, schema or event is added or changed. What the slice names:

- **The sync target** — one phony target in a generated Makefile with a Python service; its recipe is the family's
  verify script with `--install-only`. It has no state of its own: `uv sync --locked` decides what there is to do.
- **The model tooling's marker** — `scripts/event-model/node_modules/.package-lock.json`, the file npm writes for
  what it installed. It is a make dependency, newer or older than the two manifests, never a verdict (D91).
- **The model tooling's lockfile** — `scripts/event-model/package-lock.json`, shipped by the factory and tracked by
  the project; `lockfileVersion` 3; its root entry equals the manifest's pins.
- **`VERIFY_ORDER`** — a make variable the gate's recipe hands its own sub-make; it exists for the length of that
  run and is read by nothing but the Makefile's own conditional.

The verify stamp (S03) is unchanged: its key, its file and its script.
