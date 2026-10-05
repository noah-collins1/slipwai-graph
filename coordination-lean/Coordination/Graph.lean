/-!
# Layer 1 — the active domain coordination graph (§8.5 item 1, §8.2.3 Theorem targets A and B)

Nodes are slice specifications, identified by `Fin n`.  Edges are direct MCP contracts.
We store an undirected edge as an ordered pair with distinct endpoints.  Domain labels are
*annotations* and never appear in a proof: every bound below depends on degree only, which
is exactly the paper's "cross-domain edges remain legal" clause.

Nothing here needs Mathlib; the project builds on core Lean 4 alone.
-/

namespace Coordination

/-- A direct MCP contract between two slices.  `src ≠ dst` is enforced by `Graph.noLoops`. -/
structure Edge (n : Nat) where
  src : Fin n
  dst : Fin n
  deriving DecidableEq, Repr

/-- Does edge `e` touch node `v`? -/
def Edge.incident {n : Nat} (e : Edge n) (v : Fin n) : Bool :=
  e.src == v || e.dst == v

/-- The active ordinary-domain coordination graph `G = (V, E)` with `|V| = n`. -/
structure Graph (n : Nat) where
  edges   : List (Edge n)
  noLoops : ∀ e ∈ edges, e.src ≠ e.dst

variable {n : Nat}

/-- MCP degree of a node: the number of contracts incident to it. -/
def degList (es : List (Edge n)) (v : Fin n) : Nat :=
  es.countP (fun e => e.incident v)

def Graph.degree (G : Graph n) (v : Fin n) : Nat := degList G.edges v

def Graph.edgeCount (G : Graph n) : Nat := G.edges.length

/-- `Σ_{v ∈ V} deg v`, as a sum over `Fin n`. -/
def sumDegList (es : List (Edge n)) : Nat :=
  ((List.finRange n).map (degList es)).sum

def Graph.sumDeg (G : Graph n) : Nat := sumDegList G.edges

/-- The architectural invariant: every ordinary-domain slice exposes at most `Δ` contracts. -/
def Graph.BoundedDegree (G : Graph n) (Δ : Nat) : Prop :=
  ∀ v : Fin n, G.degree v ≤ Δ

/-! ### Elementary list sums -/

theorem sum_map_add {α : Type} (l : List α) (f g : α → Nat) :
    (l.map (fun x => f x + g x)).sum = (l.map f).sum + (l.map g).sum := by
  induction l with
  | nil => simp
  | cons a l ih => simp [List.map_cons, List.sum_cons, ih]; omega

theorem sum_map_le_length_mul {α : Type} (l : List α) (f : α → Nat) (B : Nat)
    (h : ∀ x ∈ l, f x ≤ B) : (l.map f).sum ≤ l.length * B := by
  induction l with
  | nil => simp
  | cons a l ih =>
    simp only [List.map_cons, List.sum_cons, List.length_cons]
    have ha := h a (List.mem_cons_self)
    have ih' := ih (fun x hx => h x (List.mem_cons_of_mem a hx))
    rw [Nat.succ_mul]; omega

/-- Count of a Boolean indicator over `finRange n`: an indicator of a single node sums to `1`. -/
theorem sum_indicator_eq_one (a : Fin n) :
    ((List.finRange n).map (fun v => if a = v then 1 else 0)).sum = 1 := by
  have hmem := List.mem_finRange a
  have hnd  := List.nodup_finRange n
  -- generalise over an arbitrary nodup list containing `a`
  suffices h : ∀ (l : List (Fin n)), l.Nodup → a ∈ l →
      (l.map (fun v => if a = v then 1 else 0)).sum = 1 from h _ hnd hmem
  intro l hnd hmem
  induction l with
  | nil => simp at hmem
  | cons b l ih =>
    simp only [List.map_cons, List.sum_cons]
    rcases List.mem_cons.mp hmem with hab | hal
    · subst hab
      have hnot : a ∉ l := (List.nodup_cons.mp hnd).1
      have : (l.map (fun v => if a = v then 1 else 0)).sum = 0 := by
        clear ih hmem hnd
        induction l with
        | nil => rfl
        | cons c l ih2 =>
          simp only [List.map_cons, List.sum_cons]
          have hac : a ≠ c := fun h => hnot (h ▸ List.mem_cons_self)
          have : a ∉ l := fun h => hnot (List.mem_cons_of_mem c h)
          simp [hac, ih2 this]
      simp [this]
    · have hab : a ≠ b := by
        intro h; subst h; exact (List.nodup_cons.mp hnd).1 hal
      simp [hab, ih (List.nodup_cons.mp hnd).2 hal]

/-- Incidence of an edge with distinct endpoints is the sum of two single-node indicators. -/
theorem incident_split (e : Edge n) (hne : e.src ≠ e.dst) (v : Fin n) :
    (if e.incident v then 1 else 0)
      = (if e.src = v then 1 else 0) + (if e.dst = v then 1 else 0) := by
  unfold Edge.incident
  by_cases h1 : e.src = v <;> by_cases h2 : e.dst = v <;> simp [h1, h2]
  exact hne (h1.trans h2.symm)

/-- Each loop-free edge contributes exactly `2` to the degree sum. -/
theorem sum_incident_eq_two (e : Edge n) (hne : e.src ≠ e.dst) :
    ((List.finRange n).map (fun v => if e.incident v then 1 else 0)).sum = 2 := by
  have : (fun v : Fin n => if e.incident v then 1 else 0)
       = fun v => (if e.src = v then 1 else 0) + (if e.dst = v then 1 else 0) := by
    funext v; exact incident_split e hne v
  rw [this, sum_map_add, sum_indicator_eq_one, sum_indicator_eq_one]

theorem degList_cons (e : Edge n) (es : List (Edge n)) (v : Fin n) :
    degList (e :: es) v = (if e.incident v then 1 else 0) + degList es v := by
  unfold degList; rw [List.countP_cons]
  by_cases h : e.incident v = true <;> simp [h] <;> omega

/-! ### The handshaking identity -/

theorem sum_map_zero {α : Type} (l : List α) : (l.map (fun _ => (0 : Nat))).sum = 0 := by
  induction l with
  | nil => rfl
  | cons a l ih => simp [List.map_cons, List.sum_cons, ih]

theorem sumDegList_eq (es : List (Edge n)) (h : ∀ e ∈ es, e.src ≠ e.dst) :
    sumDegList es = 2 * es.length := by
  induction es with
  | nil =>
    have hz : degList ([] : List (Edge n)) = fun _ => 0 := by funext v; rfl
    simp only [sumDegList, hz, sum_map_zero, List.length_nil]
  | cons e es ih =>
    have he := h e List.mem_cons_self
    have hrest := ih (fun x hx => h x (List.mem_cons_of_mem e hx))
    unfold sumDegList at *
    have : (List.finRange n).map (degList (e :: es))
         = (List.finRange n).map (fun v => (if e.incident v then 1 else 0) + degList es v) := by
      apply List.map_congr_left; intro v _; exact degList_cons e es v
    rw [this, sum_map_add, sum_incident_eq_two e he, hrest, List.length_cons]; omega

/-- **Handshaking.** `Σ_v deg v = 2|E|`. -/
theorem Graph.handshake (G : Graph n) : G.sumDeg = 2 * G.edgeCount :=
  sumDegList_eq G.edges G.noLoops

/-- **Linear edge count.** Under `deg v ≤ Δ` for all `v`, `2|E| ≤ Δ·n`, i.e. `|E| = O(n)`.
    Domain labels do not appear: the bound depends on degree alone. -/
theorem Graph.edges_le_of_bounded (G : Graph n) {Δ : Nat} (h : G.BoundedDegree Δ) :
    2 * G.edgeCount ≤ Δ * n := by
  rw [← G.handshake]
  unfold Graph.sumDeg sumDegList
  have := sum_map_le_length_mul (List.finRange n) (degList G.edges) Δ
    (fun v _ => h v)
  rw [List.length_finRange] at this
  rw [Nat.mul_comm]; exact this

/-! ### Theorem target A — the reference full pass and its upper bound -/

/-- One control-plane item processed by a full pass. -/
inductive Item (n : Nat) where
  | node (v : Fin n)
  | edge (e : Edge n)

/-- The reference traversal of an adjacency-list graph: every node once, every edge once. -/
def Graph.fullPass (G : Graph n) : List (Item n) :=
  (List.finRange n).map Item.node ++ G.edges.map Item.edge

/-- Functional coverage: every node is processed. -/
theorem Graph.fullPass_covers_node (G : Graph n) (v : Fin n) : Item.node v ∈ G.fullPass := by
  unfold Graph.fullPass
  exact List.mem_append_left _ (List.mem_map_of_mem (List.mem_finRange v))

/-- Functional coverage: every edge is processed. -/
theorem Graph.fullPass_covers_edge (G : Graph n) (e : Edge n) (he : e ∈ G.edges) :
    Item.edge e ∈ G.fullPass := by
  unfold Graph.fullPass
  exact List.mem_append_right _ (List.mem_map_of_mem he)

/-- The cost of the full pass is exactly `n + |E|` control-plane operations. -/
def Graph.fullPassCost (G : Graph n) : Nat := G.fullPass.length

theorem Graph.fullPassCost_eq (G : Graph n) : G.fullPassCost = n + G.edgeCount := by
  unfold Graph.fullPassCost Graph.fullPass Graph.edgeCount
  simp [List.length_append, List.length_map, List.length_finRange]

/-- **Theorem A (upper bound).** Under bounded degree, `2·cost ≤ (2 + Δ)·n`: the exact full
    pass is `O(n)` with the constant `1 + Δ/2`. -/
theorem Graph.fullPass_linear (G : Graph n) {Δ : Nat} (h : G.BoundedDegree Δ) :
    2 * G.fullPassCost ≤ (2 + Δ) * n := by
  rw [G.fullPassCost_eq]
  have := G.edges_le_of_bounded h
  rw [Nat.add_mul]; omega

/-! ### Theorem target B — leaf context is independent of `n` -/

/-- The one-hop context of a leaf agent on node `v`: `v`'s own spec plus incident contracts. -/
def Graph.leafContext (G : Graph n) (v : Fin n) : List (Edge n) :=
  G.edges.filter (fun e => e.incident v)

/-- Graph operations needed to assemble the leaf context: `1 + deg v`. -/
def Graph.leafContextCost (G : Graph n) (v : Fin n) : Nat := 1 + (G.leafContext v).length

theorem Graph.leafContextCost_eq (G : Graph n) (v : Fin n) :
    G.leafContextCost v = 1 + G.degree v := by
  unfold Graph.leafContextCost Graph.leafContext Graph.degree degList
  rw [List.countP_eq_length_filter]

/-- **Theorem B.** The leaf context costs at most `1 + Δ` operations; `n` does not appear. -/
theorem Graph.leafContext_bounded (G : Graph n) {Δ : Nat} (h : G.BoundedDegree Δ) (v : Fin n) :
    G.leafContextCost v ≤ 1 + Δ := by
  rw [G.leafContextCost_eq]; exact Nat.add_le_add_left (h v) 1

/-- Payload form: with spec payload ≤ `S` and contract summary ≤ `C`, the leaf context payload
    is at most `S + Δ·C`, again independent of `n`. -/
theorem Graph.leafPayload_bounded (G : Graph n) {Δ S C : Nat} (h : G.BoundedDegree Δ) (v : Fin n) :
    S + (G.leafContext v).length * C ≤ S + Δ * C := by
  have : (G.leafContext v).length = G.degree v := by
    unfold Graph.leafContext Graph.degree degList; rw [List.countP_eq_length_filter]
  rw [this]
  exact Nat.add_le_add_left (Nat.mul_le_mul_right C (h v)) S

/-- Does edge `e` touch any node of the leased subgraph `L`? -/
def Edge.touches (e : Edge n) (L : List (Fin n)) : Bool :=
  L.any (fun v => e.incident v)

/-- The context of a feature stream leasing `L`: owned specs plus all internal and boundary
    contracts (the MCP cut plus internal edges). -/
def Graph.subgraphContext (G : Graph n) (L : List (Fin n)) : List (Edge n) :=
  G.edges.filter (fun e => e.touches L)

theorem countP_or_le {α : Type} (l : List α) (p q : α → Bool) :
    l.countP (fun x => p x || q x) ≤ l.countP p + l.countP q := by
  induction l with
  | nil => simp
  | cons a l ih =>
    rw [List.countP_cons, List.countP_cons, List.countP_cons]
    by_cases hp : p a = true <;> by_cases hq : q a = true <;> simp [hp, hq] <;> omega

theorem touches_cons (e : Edge n) (v : Fin n) (L : List (Fin n)) :
    e.touches (v :: L) = (e.incident v || e.touches L) := by
  simp [Edge.touches, List.any_cons]

/-- The boundary-plus-internal contract count of a lease is at most the sum of its degrees. -/
theorem Graph.subgraphContext_le_sumDeg (G : Graph n) (L : List (Fin n)) :
    (G.subgraphContext L).length ≤ (L.map G.degree).sum := by
  unfold Graph.subgraphContext
  rw [← List.countP_eq_length_filter]
  induction L with
  | nil => simp [Edge.touches]
  | cons v L ih =>
    simp only [List.map_cons, List.sum_cons]
    have hf : (fun e : Edge n => e.touches (v :: L))
            = fun e => e.incident v || e.touches L := by
      funext e; exact touches_cons e v L
    rw [hf]
    have := countP_or_le G.edges (fun e => e.incident v) (fun e => e.touches L)
    have hd : G.degree v = G.edges.countP (fun e => e.incident v) := rfl
    omega

/-- **Theorem B for subgraphs.** Context work is linear in the *leased* subgraph, `|L|·(1+Δ)`,
    not in the repository. -/
theorem Graph.subgraphContext_bounded (G : Graph n) {Δ : Nat} (h : G.BoundedDegree Δ)
    (L : List (Fin n)) :
    L.length + (G.subgraphContext L).length ≤ L.length * (1 + Δ) := by
  have h1 := G.subgraphContext_le_sumDeg L
  have h2 := sum_map_le_length_mul L G.degree Δ (fun v _ => h v)
  rw [Nat.mul_add, Nat.mul_one]; omega

end Coordination
