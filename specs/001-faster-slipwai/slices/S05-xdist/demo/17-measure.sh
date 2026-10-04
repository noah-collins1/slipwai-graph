#!/bin/bash
# AC-S05-13 measurement: run from the measured project's root.
set -u
setmark() { sed -i -E "s/\"parallelSafe\": (true|false),/\"parallelSafe\": $1,/" project.json; }
t() { local s=$(date +%s.%N); "$@" > /tmp/s05demo/last.log 2>&1; local rc=$?; local e=$(date +%s.%N); printf '%.2f\t%s\n' "$(echo "$e - $s" | bc)" "$rc"; }
for mark in true false; do setmark $mark; VERIFY_FORCE=1 make verify >/dev/null 2>&1; done   # warm both
for i in 1 2 3; do
  for mark in true false; do
    setmark $mark
    printf 'test-only\t%s\t%s\t' "$mark" "$i"; t ./scripts/verify --test-only
    w=$(grep -o 'created: [0-9]*/[0-9]* workers' /tmp/s05demo/last.log); echo "  # ${w:-serial}; $(grep -E 'passed' /tmp/s05demo/last.log | tail -1)" >&2
    printf 'make verify\t%s\t%s\t' "$mark" "$i"; VERIFY_FORCE=1 t make verify
    printf 'make -j verify\t%s\t%s\t' "$mark" "$i"; VERIFY_FORCE=1 t make -j verify
  done
done
setmark true
