import Coordination.Synthesis
/-!
# Slipwai's current coordination method versus the paper's bounds

This module pins down, in the same formal vocabulary, the shape of what Slipwai does today
(as read from `src/slipwai/project/parallel_slices.py`, `commands.py`, `cruise.py` and the
runner `assets/toolkit/scripts/agents/cruise.py`) and compares it with the bounds proved in
`Graph.lean`, `LowerBound.lean` and `Synthesis.lean`.

Three mechanisms are modelled:

1. **Serial Phase 4 / split-order merges.**  After a fan-out of `L` slices, demos, merges and
   Phase 4 (adversary, mutation, full `make verify`, done-marker) run one slice at a time on
   `main`.  Each step depends on the one before it, so the synthesis "tree" is a caterpillar:
   depth `L - 1`.  The paper's balanced fan-in-`f` aggregation has depth `⌈log_f L⌉`.
2. **Whole-repository gates.**  About three full `make verify` runs per slice, each over the whole
   repository of size `R`, versus a gate scoped to the owned node and its `≤ Δ` incident
   contracts.
3. **Append-only log re-parse in the cruise runner.**  `entries()` and `delegate_use` re-read the
   whole `cruise-log.jsonl` / `cruise-stream.jsonl` every iteration, so a run of `I` iterations
   does `Σ_{i≤I} i = I(I+1)/2` work on logs instead of `I`.
-/


namespace Coordination

variable {f : Nat}

/-! ### 1. The serial tail as a caterpillar tree -/

/-- Two-child node helper (needs fan-in `f ≥ 2`). -/
def pair (hf : 2 ≤ f) (a b : STree f) : STree f :=
  .node 2 hf (fun i => if i.val = 0 then a else b)

/-- `serial hf k` merges `k + 1` slice results one after another: the shape of
    "merge into `main` in split order, then Phase 4 one slice at a time". -/
def serial (hf : 2 ≤ f) : Nat → STree f
  | 0     => .leaf
  | k + 1 => pair hf .leaf (serial hf k)

theorem sumFin_two (g : Fin 2 → Nat) : sumFin 2 g = g 0 + g 1 := by
  simp [sumFin]

theorem maxFin_two (g : Fin 2 → Nat) : maxFin 2 g = max (g 0) (g 1) := by
  simp [maxFin]

theorem pair_leaves (hf : 2 ≤ f) (a b : STree f) : (pair hf a b).leaves = a.leaves + b.leaves := by
  simp only [pair, STree.leaves]; rw [sumFin_two]; rfl

theorem pair_height (hf : 2 ≤ f) (a b : STree f) :
    (pair hf a b).height = 1 + max a.height b.height := by
  simp only [pair, STree.height]; rw [maxFin_two]; rfl

theorem serial_leaves (hf : 2 ≤ f) (k : Nat) : (serial hf k).leaves = k + 1 := by
  induction k with
  | zero => rfl
  | succ k ih => simp only [serial]; rw [pair_leaves, ih]; simp [STree.leaves]; omega

/-- **Serial depth is linear.**  Merging `k + 1` results one at a time has critical path `k`. -/
theorem serial_height (hf : 2 ≤ f) (k : Nat) : (serial hf k).height = k := by
  induction k with
  | zero => rfl
  | succ k ih => simp only [serial]; rw [pair_height, ih]; simp [STree.height]; omega

/-- `L ≤ 2^(L-2)` for `L ≥ 4`: the point from which a balanced binary merge is strictly
    shallower than a serial one. -/
theorem le_two_pow_sub_two : ∀ d : Nat, d + 4 ≤ 2 ^ (d + 2) := by
  intro d
  induction d with
  | zero => decide
  | succ d ih =>
    rw [show d + 1 + 2 = (d + 2) + 1 from rfl, Nat.pow_succ]
    omega

/-- **Separation.**  For any fan-out of `L ≥ 4` slices, a proper balanced fan-in-`f` aggregation
    exists whose depth is strictly below the serial depth `L - 1`, while covering exactly the same
    `L` results.  (For `L ≥ 4` the balanced depth is `≤ L - 2`; the real bound is `⌈log_f L⌉`,
    see `STree.exists_balanced`.) -/
theorem balanced_beats_serial (hf : 2 ≤ f) (L : Nat) (hL : 4 ≤ L) :
    ∃ t : STree f, t.leaves = L ∧ t.Proper ∧ t.height < (serial hf (L - 1)).height := by
  have hpow : L ≤ f ^ (L - 2) := by
    have h2 : L ≤ 2 ^ (L - 2) := by
      have := le_two_pow_sub_two (L - 4)
      have e1 : L - 4 + 4 = L := by omega
      have e2 : L - 4 + 2 = L - 2 := by omega
      rw [e1, e2] at this; exact this
    exact Nat.le_trans h2 (Nat.pow_le_pow_left hf _)
  obtain ⟨t, hl, hh, hp⟩ := STree.exists_balanced hf (L - 2) L (by omega) hpow
  refine ⟨t, hl, hp, ?_⟩
  rw [serial_height]; omega

/-! ### 2. Gate work: whole-repository versus scoped -/

/-- Slipwai today: about three full `make verify` runs per slice, each over the whole repository
    (`R` units: lint + typecheck + structure + tests). -/
def slipwaiGateWork (T R : Nat) : Nat := 3 * T * R

/-- Scoped gate: per slice, the owned node plus its `≤ Δ` incident contract tests. -/
def scopedGateWork (T Δ : Nat) : Nat := T * (1 + Δ)

/-- The repository is at least as large as the number of slices it contains (`R ≥ T`), so the
    whole-repo gate is `Ω(T²)` while the scoped gate is `Θ(T)` for fixed `Δ`.  Concretely,
    scoped work never exceeds whole-repo work once `T ≥ 1 + Δ`. -/
theorem scoped_le_slipwai (T R Δ : Nat) (hR : T ≤ R) (hT : 1 + Δ ≤ T) :
    scopedGateWork T Δ ≤ slipwaiGateWork T R := by
  unfold scopedGateWork slipwaiGateWork
  have h1 : T * (1 + Δ) ≤ T * T := Nat.mul_le_mul_left T hT
  have h2 : T * T ≤ T * R := Nat.mul_le_mul_left T hR
  have h3 : T * R ≤ 3 * T * R := by
    rw [Nat.mul_assoc]; exact Nat.le_mul_of_pos_left (T * R) (by omega)
  omega

/-! ### 3. Log re-parse in the cruise runner -/

/-- Re-parsing an append-only log of `i` entries at iteration `i`, summed over `I` iterations. -/
def reparseWork : Nat → Nat
  | 0     => 0
  | I + 1 => reparseWork I + (I + 1)

/-- Incremental tailing: one entry per iteration. -/
def incrementalWork (I : Nat) : Nat := I

/-- **Quadratic runner overhead.** `2 · reparseWork I = I (I + 1)`. -/
theorem reparseWork_closed (I : Nat) : 2 * reparseWork I = I * (I + 1) := by
  induction I with
  | zero => rfl
  | succ I ih =>
    simp only [reparseWork]
    rw [Nat.mul_add, ih]
    -- (I+1)(I+2) = I(I+1) + 2(I+1)
    have : (I + 1) * (I + 1 + 1) = I * (I + 1) + 2 * (I + 1) := by
      rw [Nat.add_mul, Nat.mul_add, Nat.mul_add]; omega
    omega

theorem incremental_le_reparse (I : Nat) : incrementalWork I ≤ reparseWork I := by
  induction I with
  | zero => simp [incrementalWork, reparseWork]
  | succ I ih => simp only [incrementalWork, reparseWork] at *; omega

end Coordination
