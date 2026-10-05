/-!
# Layer 3 — the recursive synthesis tree (§8.5 item 3, Theorem target C)

A planner/judge hierarchy is a rooted tree.  Leaves are worker results; an internal node is a
coordinator that consumes at most `f` child result contracts (bounded fan-in).  Coordination
*depth* is the tree height (critical path); coordination *work* is the number of coordinators.

We prove the three statements the paper asks for:

* `leaves_le_pow_height` — a fan-in-`f` tree of height `h` covers at most `f^h` leaves, so any
  tree covering `L` leaves has `f^height ≥ L`, i.e. `height ≥ ⌈log_f L⌉`  (lower bound);
* `exists_balanced` — for every `L ≤ f^h` there is a fan-in-`f` tree with exactly `L` leaves and
  height `≤ h`, so the lower bound is attained  (upper bound, hence `Θ(log_f L)` depth);
* `internal_le_leaves` — in a proper tree (every coordinator has ≥ 2 children) the number of
  coordinators is `< L`, so total aggregation work is `O(L)`; the constructed tree is proper.

`leaves t = L` is also the paper's safety invariant "aggregation cannot silently omit a required
child result": the root's coverage equals the declared work set exactly.
-/

namespace Coordination

/-- A synthesis tree with fan-in bounded by `f`. -/
inductive STree (f : Nat) where
  | leaf
  | node (k : Nat) (hk : k ≤ f) (children : Fin k → STree f)

variable {f : Nat}

/-! ### Sums and maxima over `Fin k` -/

def sumFin : (k : Nat) → (Fin k → Nat) → Nat
  | 0, _ => 0
  | k + 1, g => sumFin k (fun i => g i.castSucc) + g (Fin.last k)

def maxFin : (k : Nat) → (Fin k → Nat) → Nat
  | 0, _ => 0
  | k + 1, g => max (maxFin k (fun i => g i.castSucc)) (g (Fin.last k))

theorem sumFin_le_mul {k : Nat} (g : Fin k → Nat) (B : Nat) (h : ∀ i, g i ≤ B) :
    sumFin k g ≤ k * B := by
  induction k with
  | zero => simp [sumFin]
  | succ k ih =>
    simp only [sumFin]
    have := ih (fun i => g i.castSucc) (fun i => h _)
    have := h (Fin.last k)
    rw [Nat.succ_mul]; omega

theorem le_maxFin {k : Nat} (g : Fin k → Nat) (i : Fin k) : g i ≤ maxFin k g := by
  induction k with
  | zero => exact i.elim0
  | succ k ih =>
    simp only [maxFin]
    by_cases hi : i.val < k
    · have := ih (fun j => g j.castSucc) ⟨i.val, hi⟩
      have e : (⟨i.val, hi⟩ : Fin k).castSucc = i := Fin.ext rfl
      rw [e] at this
      exact Nat.le_trans this (Nat.le_max_left _ _)
    · have : i = Fin.last k := Fin.ext (by have := i.isLt; simp [Fin.val_last]; omega)
      rw [this]; exact Nat.le_max_right _ _

theorem maxFin_le {k : Nat} (g : Fin k → Nat) (B : Nat) (h : ∀ i, g i ≤ B) :
    maxFin k g ≤ B := by
  induction k with
  | zero => simp [maxFin]
  | succ k ih =>
    simp only [maxFin]
    exact Nat.max_le.mpr ⟨ih (fun i => g i.castSucc) (fun i => h _), h _⟩

theorem sumFin_congr {k : Nat} (g g' : Fin k → Nat) (h : ∀ i, g i = g' i) :
    sumFin k g = sumFin k g' := by
  have : g = g' := funext h
  rw [this]

/-- Everyone at least one: `k ≤ Σ g` when every `g i ≥ 1`. -/
theorem le_sumFin_of_pos {k : Nat} (g : Fin k → Nat) (h : ∀ i, 1 ≤ g i) : k ≤ sumFin k g := by
  induction k with
  | zero => simp
  | succ k ih =>
    simp only [sumFin]
    have := ih (fun i => g i.castSucc) (fun i => h _)
    have := h (Fin.last k)
    omega

/-! ### Leaves, height, coordinators -/

def STree.leaves : STree f → Nat
  | .leaf => 1
  | .node k _ c => sumFin k (fun i => (c i).leaves)

def STree.height : STree f → Nat
  | .leaf => 0
  | .node k _ c => 1 + maxFin k (fun i => (c i).height)

/-- Number of coordinators (internal nodes): the total aggregation work. -/
def STree.internal : STree f → Nat
  | .leaf => 0
  | .node k _ c => 1 + sumFin k (fun i => (c i).internal)

/-- Every coordinator aggregates at least two children. -/
def STree.Proper : STree f → Prop
  | .leaf => True
  | .node k _ c => 2 ≤ k ∧ ∀ i, (c i).Proper

/-! ### Theorem C, lower bound: `L ≤ f ^ height` -/

theorem STree.leaves_le_pow_height (hf : 1 ≤ f) (t : STree f) : t.leaves ≤ f ^ t.height := by
  induction t with
  | leaf => simp [STree.leaves, STree.height]
  | node k hk c ih =>
    simp only [STree.leaves, STree.height]
    have hb : ∀ i, (c i).leaves ≤ f ^ maxFin k (fun i => (c i).height) := by
      intro i
      exact Nat.le_trans (ih i)
        (Nat.pow_le_pow_right hf (le_maxFin (fun i => (c i).height) i))
    have := sumFin_le_mul (fun i => (c i).leaves) _ hb
    rw [Nat.add_comm, Nat.pow_succ']
    exact Nat.le_trans this (Nat.mul_le_mul_right _ hk)

/-- Reformulation: a tree covering `L` leaves has height at least `⌈log_f L⌉`, stated as
    "`height < h → L ≤ f^(h-1)`" to avoid a logarithm. -/
theorem STree.height_lower (hf : 1 ≤ f) (t : STree f) (h : Nat) (hh : t.height < h) :
    t.leaves ≤ f ^ (h - 1) :=
  Nat.le_trans (t.leaves_le_pow_height hf) (Nat.pow_le_pow_right hf (by omega))

/-! ### Theorem C, upper bound: a balanced tree attains the bound -/

/-- Extend `g : Fin k → Nat` by one last value. -/
def extendFin {k : Nat} (g : Fin k → Nat) (x : Nat) : Fin (k + 1) → Nat :=
  fun i => if h : i.val < k then g ⟨i.val, h⟩ else x

theorem extendFin_castSucc {k : Nat} (g : Fin k → Nat) (x : Nat) (i : Fin k) :
    extendFin g x i.castSucc = g i := by
  simp [extendFin, Fin.castSucc, Fin.castAdd, Fin.castLE, i.isLt]

theorem extendFin_last {k : Nat} (g : Fin k → Nat) (x : Nat) :
    extendFin g x (Fin.last k) = x := by
  simp [extendFin, Fin.last]

/-- Recursive decomposition covers the parent's declared work set: `L` leaves can be split
    among `k` children with each child getting between `1` and `B` leaves, provided
    `k ≤ L ≤ k·B`. -/
theorem split_work (B : Nat) (hB : 1 ≤ B) :
    ∀ (k L : Nat), k ≤ L → L ≤ k * B →
      ∃ g : Fin k → Nat, sumFin k g = L ∧ ∀ i, 1 ≤ g i ∧ g i ≤ B := by
  intro k
  induction k with
  | zero =>
    intro L _ hL
    refine ⟨fun i => i.elim0, ?_, fun i => i.elim0⟩
    simp [sumFin]; omega
  | succ k ih =>
    intro L hkL hL
    -- the last child takes `min B (L - k)`; the rest is still splittable among `k` children
    let x := min B (L - k)
    have hx1 : 1 ≤ x := by
      have : 1 ≤ L - k := by omega
      exact Nat.le_min.mpr ⟨hB, this⟩
    have hxB : x ≤ B := Nat.min_le_left _ _
    have hxL : x ≤ L - k := Nat.min_le_right _ _
    have hrest1 : k ≤ L - x := by omega
    have hrest2 : L - x ≤ k * B := by
      rw [Nat.succ_mul] at hL
      by_cases hc : B ≤ L - k
      · have : x = B := Nat.min_eq_left hc
        omega
      · have : x = L - k := Nat.min_eq_right (by omega)
        have : L - x = k := by omega
        rw [this]; exact Nat.le_mul_of_pos_right k hB
    obtain ⟨g, hsum, hbnd⟩ := ih (L - x) hrest1 hrest2
    refine ⟨extendFin g x, ?_, ?_⟩
    · simp only [sumFin]
      rw [sumFin_congr _ g (fun i => extendFin_castSucc g x i), extendFin_last, hsum]
      omega
    · intro i
      by_cases hi : i.val < k
      · have e : i = (⟨i.val, hi⟩ : Fin k).castSucc := Fin.ext rfl
        rw [e, extendFin_castSucc]; exact hbnd _
      · have : i = Fin.last k := Fin.ext (by have := i.isLt; simp [Fin.val_last]; omega)
        rw [this, extendFin_last]; exact ⟨hx1, hxB⟩

/-- **Theorem C (upper bound).** For `f ≥ 2` and any `L ≥ 1` with `L ≤ f^h`, there is a
    proper fan-in-`f` tree with exactly `L` leaves and height `≤ h`.  Together with
    `leaves_le_pow_height` the minimal height is exactly `⌈log_f L⌉`. -/
theorem STree.exists_balanced (hf : 2 ≤ f) :
    ∀ (h L : Nat), 1 ≤ L → L ≤ f ^ h →
      ∃ t : STree f, t.leaves = L ∧ t.height ≤ h ∧ t.Proper := by
  intro h
  induction h with
  | zero =>
    intro L hL1 hL
    simp at hL
    have : L = 1 := by omega
    subst this
    exact ⟨.leaf, rfl, Nat.le_refl _, trivial⟩
  | succ h ih =>
    intro L hL1 hL
    by_cases hL2 : L ≤ 1
    · have : L = 1 := by omega
      subst this
      exact ⟨.leaf, rfl, Nat.zero_le _, trivial⟩
    · -- L ≥ 2: split among k = min f L ≥ 2 children, each ≤ f^h leaves
      have hpow : 1 ≤ f ^ h := Nat.pow_pos (by omega)
      let k := min f L
      have hk  : k ≤ f := Nat.min_le_left _ _
      have hkL : k ≤ L := Nat.min_le_right _ _
      have hk2 : 2 ≤ k := Nat.le_min.mpr ⟨hf, by omega⟩
      have hLk : L ≤ k * f ^ h := by
        by_cases hc : f ≤ L
        · have : k = f := Nat.min_eq_left hc
          rw [this, ← Nat.pow_succ']; exact hL
        · have : k = L := Nat.min_eq_right (by omega)
          rw [this]; exact Nat.le_mul_of_pos_right L hpow
      obtain ⟨g, hsum, hbnd⟩ := split_work (f ^ h) hpow k L hkL hLk
      -- choose a child tree for every part
      have hch : ∀ i : Fin k, ∃ t : STree f, t.leaves = g i ∧ t.height ≤ h ∧ t.Proper :=
        fun i => ih (g i) (hbnd i).1 (hbnd i).2
      obtain ⟨c, hc⟩ := Classical.axiomOfChoice hch
      refine ⟨.node k hk c, ?_, ?_, ?_⟩
      · simp only [STree.leaves]
        rw [sumFin_congr _ g (fun i => (hc i).1)]; exact hsum
      · simp only [STree.height]
        have : maxFin k (fun i => (c i).height) ≤ h :=
          maxFin_le _ h (fun i => (hc i).2.1)
        omega
      · exact ⟨hk2, fun i => (hc i).2.2⟩

/-! ### Theorem C, total work: coordinators `< L` in a proper tree -/

theorem STree.leaves_pos_of_proper (t : STree f) (hp : t.Proper) : 1 ≤ t.leaves := by
  induction t with
  | leaf => simp [STree.leaves]
  | node k hk c ih =>
    simp only [STree.leaves]
    obtain ⟨hk2, hpc⟩ := hp
    have := le_sumFin_of_pos (fun i => (c i).leaves) (fun i => ih i (hpc i))
    omega

/-- **Theorem C (work).** Every coordinator has at least two children, so there are fewer
    coordinators than leaves: total aggregation work is `O(L)`. -/
theorem STree.internal_lt_leaves (t : STree f) (hp : t.Proper) : t.internal < t.leaves := by
  induction t with
  | leaf => simp [STree.internal, STree.leaves]
  | node k hk c ih =>
    simp only [STree.internal, STree.leaves]
    obtain ⟨hk2, hpc⟩ := hp
    -- Σ internal ≤ Σ (leaves - 1) = Σ leaves - k, and k ≥ 2
    have key : ∀ (k : Nat) (c : Fin k → STree f), (∀ i, (c i).Proper) →
        (∀ i, (c i).internal < (c i).leaves) →
        sumFin k (fun i => (c i).internal) + k ≤ sumFin k (fun i => (c i).leaves) := by
      intro k
      induction k with
      | zero => intro _ _ _; simp [sumFin]
      | succ k ihk =>
        intro c hpc hlt
        simp only [sumFin]
        have := ihk (fun i => c i.castSucc) (fun i => hpc _) (fun i => hlt _)
        have := hlt (Fin.last k)
        omega
    have := key k c hpc (fun i => ih i (hpc i))
    omega

end Coordination
