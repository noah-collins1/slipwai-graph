/-!
# Layer 2 — the adversary lower bound for an exact full pass (§8.5 item 2, Theorem target A)

Input-access model.  The active graph state has `m` fields (one validity bit per node and per
edge, so `m = n + |E|`).  An exact algorithm is a *deterministic decision tree*: at each step it
reads one field and branches; at a leaf it answers.  The cost of a run is the number of fields
read.

The control-plane question is "is every active node and contract valid?", i.e. the conjunction
of all `m` fields.  We prove: any decision tree that computes this conjunction correctly on
*every* input must read **all** `m` fields on the all-valid input.  Hence worst-case cost is
`≥ m = n + |E|`, which matches the `n + |E|` upper bound of `Graph.fullPass` exactly.
-/

namespace Coordination

/-- A deterministic adaptive algorithm over `m` Boolean fields. -/
inductive DTree (m : Nat) where
  | leaf  (out : Bool)
  | query (i : Fin m) (ifTrue ifFalse : DTree m)

variable {m : Nat}

/-- The answer the algorithm gives on input `x`. -/
def DTree.eval : DTree m → (Fin m → Bool) → Bool
  | .leaf b, _ => b
  | .query i t f, x => if x i then t.eval x else f.eval x

/-- The fields the algorithm reads on input `x`, in order. -/
def DTree.reads : DTree m → (Fin m → Bool) → List (Fin m)
  | .leaf _, _ => []
  | .query i t f, x => i :: (if x i then t.reads x else f.reads x)

/-- Cost of a run = number of field reads. -/
def DTree.cost (t : DTree m) (x : Fin m → Bool) : Nat := (t.reads x).length

/-- "Every active node and every active contract is valid." -/
def allValid (x : Fin m → Bool) : Bool := (List.finRange m).all x

/-- The all-valid input. -/
def allOnes : Fin m → Bool := fun _ => true

/-- `x` with field `i` flipped. -/
def flipAt (x : Fin m → Bool) (i : Fin m) : Fin m → Bool :=
  fun j => if j = i then !x j else x j

theorem allValid_allOnes : allValid (allOnes (m := m)) = true := by
  unfold allValid allOnes; simp [List.all_eq_true]

theorem allValid_flip_allOnes (i : Fin m) : allValid (flipAt allOnes i) = false := by
  unfold allValid
  apply Bool.eq_false_iff.mpr
  intro h
  have := (List.all_eq_true.mp h) i (List.mem_finRange i)
  simp [flipAt, allOnes] at this

theorem flipAt_agree (x : Fin m → Bool) (i j : Fin m) (hij : j ≠ i) :
    flipAt x i j = x j := by
  simp [flipAt, hij]

/-- Core adversary lemma, generalised over a set `S` of fields already fixed to `true`.
    If `t` is correct on every input agreeing with `allOnes` on `S`, then on `allOnes` it
    reads every field outside `S`. -/
theorem DTree.reads_all_aux (t : DTree m) :
    ∀ (S : List (Fin m)),
      (∀ x : Fin m → Bool, (∀ j ∈ S, x j = true) → t.eval x = allValid x) →
      ∀ i : Fin m, i ∉ S → i ∈ t.reads allOnes := by
  induction t with
  | leaf b =>
    intro S hc i hi
    exfalso
    have h1 := hc allOnes (fun _ _ => rfl)
    have h2 := hc (flipAt allOnes i) (by
      intro j hj
      have hji : j ≠ i := fun h => hi (h ▸ hj)
      rw [flipAt_agree _ _ _ hji]; rfl)
    simp only [DTree.eval] at h1 h2
    rw [allValid_allOnes] at h1
    rw [allValid_flip_allOnes] at h2
    rw [h1] at h2; exact Bool.noConfusion h2
  | query k tt ff iht _ =>
    intro S hc i hi
    simp only [DTree.reads, allOnes, ite_true]
    by_cases hik : i = k
    · exact hik ▸ List.mem_cons_self
    · apply List.mem_cons_of_mem
      -- restrict to inputs that also fix `k` to true; there `query k tt ff` behaves as `tt`
      have hc' : ∀ x : Fin m → Bool, (∀ j ∈ k :: S, x j = true) → tt.eval x = allValid x := by
        intro x hx
        have hk : x k = true := hx k List.mem_cons_self
        have := hc x (fun j hj => hx j (List.mem_cons_of_mem k hj))
        simp only [DTree.eval, hk, ite_true] at this
        exact this
      have hi' : i ∉ k :: S := by
        intro h; rcases List.mem_cons.mp h with h | h
        · exact hik h
        · exact hi h
      exact iht (k :: S) hc' i hi'

/-- **Adversary lemma.** A correct exact validator reads every field on the all-valid input. -/
theorem DTree.reads_all (t : DTree m) (hc : ∀ x, t.eval x = allValid x) (i : Fin m) :
    i ∈ t.reads allOnes :=
  t.reads_all_aux [] (fun x _ => hc x) i (by simp)

/-- **Theorem A (lower bound).** Worst-case cost of any exact validator is at least `m`. -/
theorem DTree.cost_lower_bound (t : DTree m) (hc : ∀ x, t.eval x = allValid x) :
    m ≤ t.cost allOnes := by
  unfold DTree.cost
  have hsub : (List.finRange m) ⊆ t.reads allOnes := fun i _ => t.reads_all hc i
  have := List.Nodup.length_le_of_subset (List.nodup_finRange m) hsub
  rwa [List.length_finRange] at this

end Coordination
