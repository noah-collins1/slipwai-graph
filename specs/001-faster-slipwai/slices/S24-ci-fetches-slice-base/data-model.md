# Data model — S24-ci-fetches-slice-base

No stored shape changes. Two things generated are said more exactly:

- **The `verify` job's checkout** — in `.github/workflows/verify.yml` (generated) and `verify-delivery.yml`
  (adopted): `actions/checkout@v6` with `fetch-depth: 0`. In the adopted GitLab job, `verify-delivery` carries
  `variables: GIT_DEPTH: "0"`. Every other job's checkout is one commit, as before.
- **`check-slice-scope`'s exit in a forge's checkout** — 0 where the branch is not `slice/<id>`, where the slice
  is inside its scope, and where git cannot read the checkout at all; 1 for a refused path, a lost record, no base
  to compare with, and a comparison git could not run.
