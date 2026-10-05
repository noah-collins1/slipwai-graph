# coordination-lean

Machine-checked versions of the §8.2.3 / §8.5 theorem targets in *The Coordination Tax* (Sedlacek, v6),
plus a formal model of Slipwai's current coordination loop for the big-O comparison.

Core Lean 4 only (no Mathlib). Toolchain is pinned in `lean-toolchain` (v4.34.1).

```sh
~/.elan/bin/lake build          # all five modules; exit 0, no sorry
```

| Module | Paper layer | Main results |
|---|---|---|
| `Coordination/Graph.lean` | §8.5 item 1, Theorems A and B | `Graph.handshake` (Σdeg = 2\|E\|), `Graph.edges_le_of_bounded` (2\|E\| ≤ Δn), `Graph.fullPass_linear` (2·cost ≤ (2+Δ)n), `Graph.leafContext_bounded` (≤ 1+Δ, no `n`), `Graph.subgraphContext_bounded` (≤ \|L\|(1+Δ)) |
| `Coordination/LowerBound.lean` | §8.5 item 2, Theorem A lower bound | `DTree.cost_lower_bound`: any exact validator reads all `m = n + \|E\|` fields on the all-valid input, so the full pass is Θ(n+\|E\|) |
| `Coordination/Synthesis.lean` | §8.5 item 3, Theorem C | `STree.leaves_le_pow_height` (L ≤ f^height), `STree.exists_balanced` (height ≤ h whenever L ≤ f^h, proper tree), `STree.internal_lt_leaves` (coordinators < L) |
| `Coordination/Lease.lean` | §8.5 item 4, safety invariants | `LeaseTable.exclusive`, `acquire_preserves`, `visible_iff`, `visible_bound` (one-hop visibility) |
| `Coordination/Comparison.lean` | Slipwai today vs paper | `serial_height` (serial Phase 4 depth = L−1), `balanced_beats_serial` (L ≥ 4), `scoped_le_slipwai` (gate work), `reparseWork_closed` (runner log overhead I(I+1)/2) |

Every theorem depends only on `propext`, `Classical.choice`, `Quot.sound` (check with `#print axioms`).

What is *not* formalised, by the paper's own scoping: the cost of finding a good decomposition
(graph partitioning), model-capability claims (H7), and anything about LLM inference time.
The cost model counts control-plane graph operations and gate units, not tokens or seconds.
