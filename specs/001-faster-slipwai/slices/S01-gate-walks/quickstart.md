# Quickstart: S01-gate-walks — the demo

Run from this checkout. Everything is written under a scratch directory; nothing here changes.

```sh
D=$(mktemp -d) && ./slipwai generate shop --profile event-modelling --backend python --frontend react-vite \
  --output "$D" --skip-checks --no-init --no-install && cd "$D/shop"
```

1. **The count.** `make check-imports` → `check-imports: inward dependency rule holds (79 directory entries read)`;
   `make check-migrations` → today's sentence, then the same count.
2. **Pruned directories cost one entry each.** `mkdir -p apps/service/.venv/lib/pkg/domain apps/web/node_modules/pkg`
   and put a few hundred files in them, one a `domain/` file holding `from ..adapters.store import save`; both gates
   pass and each count is higher by two.
3. **A real violation is still found.** Put `from ..adapters.store import save` in a new file under
   `apps/service/src/shop/domain/` (the generated domain); `make check-imports` fails naming it, with no count.
   (The gate reads an import line for a layer name between separators — `..adapters.store`, not a bare
   `..adapters import`; that is how it read before this slice too.)
4. **`target` is read unless it is Maven's.** `mkdir -p apps/service/src/target/domain` with the same line in a
   file there → fails. In a Java project (`--backend java-quarkus`), a `target/` beside `pom.xml` holding a
   `DROP TABLE` migration → `make check-migrations` passes.
5. **The code index on a slice branch.** With `codegraph` on `PATH`: `./init --extension codegraph`, commit,
   `make check-codegraph` on `main` (today's line), `git checkout -b slice/S1`, `make check-codegraph` → `hashed 0
   of N … the integrity check was not run here: it runs on the trunk, on any other branch and in CI` (a file written within two
   seconds of the run that last vouched for it is hashed again; an uncommitted edit is hashed on every run until
   it is committed); edit one source file, `scripts/codegraph sync`, run again → `hashed 1 of N`; `CI=true make
   check-codegraph` → today's line. Without the CLI, the stand-in the tests use (`FAKE_CODEGRAPH` in
   `tests/test_code_index_health.py`, put on `PATH` as `codegraph`) builds a real SQLite index the gate reads.

Expected: the gates say what they read, skip what is not the project's, and still fail what they failed.
