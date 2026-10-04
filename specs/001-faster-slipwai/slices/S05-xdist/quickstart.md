# Quickstart: S05-xdist

```sh
./slipwai generate shop --backend python --output /tmp/x --no-init --no-install --skip-checks
cd /tmp/x/shop && grep parallelSafe project.json        # "parallelSafe": true
make test                                               # pytest … -n auto --maxprocesses 4
# opt out: set "parallelSafe": false in project.json, then
make test                                               # pytest as before, serial
```
