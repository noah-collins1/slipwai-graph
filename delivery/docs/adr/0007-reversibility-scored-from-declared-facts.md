# 0007. A decision's reversibility tier is scored from facts declared when the entry is written

Date: 2026-10-07

## Status

Proposed

Drafted by `/cruise` iteration 27 of `001-faster-slipwai`, at the pre-planning gaps stage of `S26-reversibility-line`
(decision D174 in `specs/001-faster-slipwai/decisions.md`). The run never accepts its own architecture decision; the
word `Accepted` here is a person's.

## Context

FR-029 and FR-051 require every decision entry to carry `Reversibility: easy|guarded|hard`, scored by a fail-closed
classifier over factual booleans and enums. Most decisions are written before any commit exists: D54, the case that
motivated User Story 8, never had commits, and its *Written to* names only record files. Three readers depend on the
line: `S27` acts on the tier, `S28` attaches revert ranges, and `S39`'s `measures.py` (D168) counts tiers and
escalations. Decision logs are append-only, records are never reclassified (FR-050), and logs written by earlier
releases must keep passing (D65).

## Decision

The entry's writer — the host for a stage-recommendation entry, the skipper for the entry it returns — declares each
FR-051 fact about what accepting the decision would change, and runs one shipped scoring verb. Dependants are read
from the entry's `Scope:` line. The line puts the tier first (or a one-tier-at-a-time escalation chain, D177), then the
version of the rules that scored it, then the facts. `check-decisions` re-derives the tier under the named rules
version and refuses a disagreement, an unknown key (`size` and `urgency` among them, D176) and a second line; a known
fact that is missing or carries an unrecognised value scores `hard`. Whether a file is one `migrate` propagates is
looked up in a committed list (D175): an adopted
repository's `delivery/.written`, a generated project's `.slipwai/propagated`, which names the method categories only
(D183) — so CI workflows, which `migrate` also carries, are held by the declared `ci_workflow` fact and not by the list. Once commits exist, a later check (`S28`) may raise a tier by writing a
superseding record; it never edits or lowers one.

## Consequences

Pre-commit decisions such as D54 get a tier a developer can check, deterministic and verifiable by the gate alone, and
old logs keep passing. The tier is only as honest as the declared facts until `S28`'s check exists, so an
under-declared entry can pass as `easy` meanwhile; the fail-closed defaults and FR-057's misclassification measure are
the guard. Every line written in this shape is permanent: a later move to facts derived from commits means readers
accept both shapes indefinitely, and the gate keeps every rules version it has shipped so that old lines can be
re-derived.
