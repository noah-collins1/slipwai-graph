# Quickstart: S33-factory-gate-stamp

Once `s33.patch` is applied and committed, on `adopt-method` (not the trunk) with no CI variable set:

```sh
make verify            # the full gate, about forty minutes; ends `verify: all gates passed`
make verify            # unchanged tree: one line saying it already passed, and when; well under a second
VERIFY_FORCE=1 make verify   # every check again
make verify TESTS=test_changelog   # a slice of the suite: runs as before, reads and writes no stamp
```
