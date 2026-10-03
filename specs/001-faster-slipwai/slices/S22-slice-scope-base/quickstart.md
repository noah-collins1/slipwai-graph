# Quickstart — S22-slice-scope-base

What proves the slice, run from this checkout. No seed data, no service, no port.

## Setup: a repository adopted at its root, on a slice branch with a host-surface change committed

```sh
FACTORY=$(pwd); T=$(mktemp -d); cp -r tests/fixtures/adopt/python-worker "$T/repo"; cd "$T/repo"
git init -q -b main && git add -A && git -c user.name=t -c user.email=t@local commit -q -m theirs
"$FACTORY/slipwai" adopt --yes          # makes its own commit on main
git checkout -q -b slice/S1
echo "x:" >> Makefile && git -c user.name=t -c user.email=t@local commit -q -am "a host change"
make -f delivery/Makefile check-slice-scope
```

Expect: exit non-zero; the header ends *compared with `main` at <commit>*; `Makefile: outside every deployable`.

## 1. A minted base no longer empties the check

```sh
git branch master HEAD;                       make -f delivery/Makefile check-slice-scope; git branch -D master
git update-ref refs/remotes/origin/master HEAD; make -f delivery/Makefile check-slice-scope; git update-ref -d refs/remotes/origin/master
git tag main HEAD;                            make -f delivery/Makefile check-slice-scope; git tag -d main
```

Expect, each time: exit non-zero, `Makefile` refused. (Before the slice: exit 0, *touches only what one slice may*.)

## 2. A branch cannot name itself the trunk

```sh
python3 - <<'PY'
import json; d = json.load(open("project.json")); d.setdefault("ci", {})["branch"] = "slice/S1"
json.dump(d, open("project.json", "w"))
PY
make -f delivery/Makefile check-slice-scope; git checkout -- project.json
```

Expect: exit non-zero; `project.json` and `Makefile` both refused.

## 3. A developer's checkout with no trunk fails with what to run

```sh
git clone -q --depth 1 --branch slice/S1 "file://$T/repo" "$T/shallow" && cd "$T/shallow"
make -f delivery/Makefile check-slice-scope
```

Expect: exit non-zero and one line of its own, under no header, naming `main` and the command to run:
`git fetch origin main:refs/remotes/origin/main`. (Before: exit 0, *nothing to hold*.)

```sh
git fetch -q origin main:refs/remotes/origin/main; make -f delivery/Makefile check-slice-scope
git fetch -q --unshallow origin;                   make -f delivery/Makefile check-slice-scope
```

Expect: after the first fetch, exit non-zero and one line saying the branch *shares no history with `main` at this
depth* and naming `git fetch --unshallow origin`; after the second, a verdict — exit non-zero with `Makefile`
refused, *compared with `main` at <commit>*: each command the gate printed did what its line said.

## 4. A forge's pull-request checkout says it did not check

```sh
rm -rf "$T/ci" && git clone -q --depth 1 --branch slice/S1 "file://$T/repo" "$T/ci" && cd "$T/ci"
git checkout -q --detach && GITHUB_HEAD_REF=slice/S1 make -f delivery/Makefile check-slice-scope; echo "exit $?"
git checkout -q slice/S1 && CI=true make -f delivery/Makefile check-slice-scope; echo "exit $?"
```

Expect, both times (a detached pull-request checkout; any run with a CI marker set, D32): exit 0; on stderr
*slice/S1 was NOT checked* and `fetch-depth: 0`; no `git fetch` command and the words *nothing to hold* nowhere.

## 5. `HEAD` is never the trunk, and an unrecorded `master` trunk is told what to record

```sh
cd "$T/repo" && python3 - <<'PY'
import json; d = json.load(open("project.json")); d.setdefault("ci", {})["branch"] = "HEAD"
json.dump(d, open("project.json", "w"))
PY
make -f delivery/Makefile check-slice-scope; git checkout -- project.json
```

Expect: exit non-zero; `project.json` and `Makefile` refused; the header says `ci.branch` names `HEAD`, which is not
a branch name. (`tests/test_slice_scope_report.py` `MasterBesideMainTest` shows the `master` clause of D33.)

## 6. An honest slice is as it was

```sh
cd "$T/repo" && git reset -q --hard main && echo "# a slice's test" >> tests/test_scope_demo.py
make -f delivery/Makefile check-slice-scope
```

Expect: exit 0, `check-slice-scope: slice/S1 touches only what one slice may (compared with `main` at <commit>)`.

## 7. The gates

`make verify` and `make -f delivery/Makefile verify` in this checkout — both green.
