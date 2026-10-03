# Data model: S02-runner-bookkeeping

Nothing new is stored on disk but one optional object and one optional line.

**In the runner's process only (never written):**

| Record | Holds | Used where |
|---|---|---|
| Vouched hash, per file | SHA-256 of the bytes; size, modification and change time in nanoseconds, identity (device, inode), taken from the file as it was opened; the moment it was hashed | Controls (D56: all four facts or the file is hashed every time) and `specs/` (D57: as many as the platform reports). Reused only where every fact reads as recorded and the file's times are two seconds older than the hashing |
| The log as left | Entry count; the file's size, times and identity after the runner's own append | `drive()`: unchanged → no byte read; anything else → forgotten, whole read (D58) |
| The stream's marker | The byte offset and the exact marker line the runner wrote for this iteration | `index_use` is read from there when the bytes at the offset are that line (D58) |

**In `specs/cruise-log.jsonl`, per entry, optional (D58):**

| Field | Holds |
|---|---|
| `bookkeeping.log_bytes` | Bytes the runner read from the log since its previous append, or since the process started |
| `bookkeeping.stream_bytes` | Bytes it read from the raw stream for this entry; absent where no stream is kept |

`fingerprint` keeps its name and 16 hex characters; its value for a tree differs from the earlier code's (D57).

**In `decisions.md`, per entry, optional (D60):** `- **Scope:** global` or `- **Scope:** <slice id>[, <slice id>…]`,
shown directly after the Stage line. Absent, empty to the filter, or unreadable → carried as global.

**In `.codegraph/gate-memory.json`:** no new field; `health()` writes it through the gate's `remember()` (D59).
