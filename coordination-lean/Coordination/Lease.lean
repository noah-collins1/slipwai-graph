import Coordination.Graph
/-!
# Layer 4 — architectural safety invariants (§8.5 item 4)

The L1 lease is a *human-held ownership claim* over spec/tool nodes.  We model it as a partial
map from nodes to owners.  Two properties the paper wants machine-checked:

* exclusive-write leases never overlap (`exclusive`), and acquiring a free node keeps every other
  lease untouched (`acquire_preserves`);
* default visibility of a leaf agent is exactly its owned nodes plus the far ends of incident
  MCP contracts — never a two-hop neighbour (`visible_iff`).
-/


namespace Coordination

variable {n : Nat} {Owner : Type}

/-- The lease table: which human (if any) holds each node. -/
structure LeaseTable (n : Nat) (Owner : Type) where
  holder : Fin n → Option Owner

def LeaseTable.owns (T : LeaseTable n Owner) (o : Owner) (v : Fin n) : Prop :=
  T.holder v = some o

/-- **Exclusivity.** A node has at most one lease holder. -/
theorem LeaseTable.exclusive (T : LeaseTable n Owner) {o o' : Owner} {v : Fin n}
    (h : T.owns o v) (h' : T.owns o' v) : o = o' := by
  unfold LeaseTable.owns at h h'
  rw [h] at h'; exact Option.some.inj h'

/-- Acquire a node that is currently free. -/
def LeaseTable.acquire (T : LeaseTable n Owner) (o : Owner) (v : Fin n)
    (_free : T.holder v = none) : LeaseTable n Owner :=
  ⟨fun w => if w = v then some o else T.holder w⟩

theorem LeaseTable.acquire_owns (T : LeaseTable n Owner) (o : Owner) (v : Fin n)
    (hfree : T.holder v = none) : (T.acquire o v hfree).owns o v := by
  simp [LeaseTable.acquire, LeaseTable.owns]

/-- **No disturbance.** Acquiring `v` changes no other node's lease. -/
theorem LeaseTable.acquire_preserves (T : LeaseTable n Owner) (o : Owner) (v w : Fin n)
    (hfree : T.holder v = none) (hw : w ≠ v) :
    (T.acquire o v hfree).holder w = T.holder w := by
  simp [LeaseTable.acquire, hw]

/-- Release a node. -/
def LeaseTable.release (T : LeaseTable n Owner) (v : Fin n) : LeaseTable n Owner :=
  ⟨fun w => if w = v then none else T.holder w⟩

theorem LeaseTable.release_free (T : LeaseTable n Owner) (v : Fin n) :
    (T.release v).holder v = none := by
  simp [LeaseTable.release]

/-- The other endpoint of an edge, as seen from `v`. -/
def Edge.other (e : Edge n) (v : Fin n) : Fin n := if e.src = v then e.dst else e.src

/-- Default visibility of owner `o`: the nodes it owns plus the far end of each incident
    contract.  Nothing two hops away is reachable without an explicit expansion event. -/
def LeaseTable.visible (T : LeaseTable n Owner) (G : Graph n) (o : Owner) (w : Fin n) : Prop :=
  T.owns o w ∨ ∃ v, T.owns o v ∧ ∃ e ∈ G.edges, e.incident v = true ∧ e.other v = w

/-- **One-hop visibility.** Visibility is *exactly* owned-or-adjacent-to-owned: this is the
    paper's one-hop context rule as a definitional invariant. -/
theorem LeaseTable.visible_iff (T : LeaseTable n Owner) (G : Graph n) (o : Owner) (w : Fin n) :
    T.visible G o w ↔
      (T.owns o w ∨ ∃ v, T.owns o v ∧ ∃ e ∈ G.edges, e.incident v = true ∧ e.other v = w) :=
  Iff.rfl

/-- A visible node that is not owned is the endpoint of a contract incident to an owned node,
    so the visible set of a leaf owning one node `v` has size at most `1 + deg v`. -/
theorem LeaseTable.visible_bound (T : LeaseTable n Owner) (G : Graph n) (o : Owner) (v : Fin n)
    (hsingle : ∀ u, T.owns o u → u = v) (w : Fin n) (hw : T.visible G o w) :
    w = v ∨ ∃ e ∈ G.leafContext v, e.other v = w := by
  rcases hw with h | ⟨u, hu, e, he, hinc, hoth⟩
  · exact Or.inl (hsingle w h)
  · right
    have := hsingle u hu; subst this
    exact ⟨e, List.mem_filter.mpr ⟨he, hinc⟩, hoth⟩

end Coordination
