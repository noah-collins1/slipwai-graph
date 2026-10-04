# Data model: S05-xdist

`project.json` gains one optional top-level key, `parallelSafe`: the JSON `true` turns the Python gate's pytest
parallel; any other value, or none, is serial. Written `true` by `generate`; carried, never added, by replay; never
written by `adopt`.
