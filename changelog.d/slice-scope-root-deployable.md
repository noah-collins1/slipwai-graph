PATCH

**`check-slice-scope` no longer refuses a slice's own code in an adopted repository.** A repository adopted
with its one application at the root records that deployable at `.`, and the gate read `.` as owning no path,
so a slice's tests and its code outside a subdirectory were all refused as *outside every deployable*. A
deployable at `.` now owns every path no deployable in a subdirectory claims; a service under `apps/` still
owns its own files, and an empty `path` still owns nothing. This asks nothing of a repository already
generated: `slipwai migrate` carries the corrected script.
