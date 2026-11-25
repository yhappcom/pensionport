# R3-04 — three-trial root-cause audit and prospective protocol redesign (2026-11-25)

## Decision and custody

User-directed transition: stop the per-item legacy repair loop. Preserve the three failed trials, their original reference packets, alignment, scores and 447 unresolved source-link tasks. This document is a design lock, not an engine release or a new accuracy score. #277 remains reserved and unread in this work. Baseline engine 8ff3a522bf1b17f212bb4d02fdb2495344311911; #288 score record 19ac34988a58aa0398a98e38d9d7f69e0dd15729, CI 45544405051 success. R3-04 HOLD; R3-05/06 BLOCKED. Prospective diagnostic allowed, not formal qualification.

## Read-only census

Read the actual frozen alignment arrays, 9 booleans per pair. No pair is reassigned. #288 frozen journal replay reproduced TP59 FP90 FN97 and score head 03b87f05de814c91f15ff63fdacac23a05810e1048c0d1b4b9d5e33bf64547e0.

| Trial | Pairs | Exact | Core-entailment true, another axis false | Core-entailment false |
|---|---:|---:|---:|---:|
|270 V2|124|60|38|26|
|271 V1|82|53|13|16|
|288 V3|143|59|57|27|
|Total|349|172|108|69|

Axis failure counts (270/271/288): speaker+stance 28/7/46; entailment 26/16/27; conditions 14/17/22; kind 13/7/27; numeric 7/6/29; hypothetical scope 6/3/30; time 0/0/22; negation 4/1/1; exceptions 0/2/0. Overlapping failures, no rate comparison across versions or inference that 108 pairs are true equivalents. Unmatched claims are not included in this census.

#288 decomposition:
- Speaker+stance 46: participant ID differs in 11, act in 25, modality in 30, polarity in 1; one pair both UNKNOWN. Overlapping counts. Speaker role is not the main cause of all 46.
- Numeric 29: 8 same coordinate sets (but differing roles/signatures), 21 differing coordinate sets. Same coordinates are not semantic truth.
- Conditions 22: 15 one empty side; 7 both nonempty with some shared exact fragments. Cannot dismiss missing condition as formatting.
- Time 22: all first 2025 vs second null. Some are inherited topic time, some time-specific projection, not automatically equivalent.
- Of 59 exact pairs, 20 have differing direct cue sets, 0 disjoint cue sets. Exact score does not certify correct atomic boundaries.
- Both first and second builders independently define role mappings, kind-to-act mapping, time assignment, reported attribution and broad direct cue ranges. Same compiler validates structure but does not make authoring conventions identical.

Archive SHA256: #270 8462e3c492d8bb1b5e72bd3c8d5cd8d72a1990a3c8338eb9d7056f7b7ddb134e; #271 c7699d0d4cc1825be81c5f7ff6dcb24fdfb06fae8eddba960d83aad2909f42d3; #288 40ec0aca35569d5bb564341a64ea47536fc69d23905b820b81becf8f881fe136.

## Root causes and regression obligations (development cases only)

1. Atomic granularity: both sides can combine separate truth-evaluable predicates, repetitions, questions and answers. Use direct evidence for each minimal proposition; broader context separate. No exact TP awarded for split/merge merely by overlapping coordinates.
2. Coupled labels: participant, act, attribution, epistemic certainty and premise are different dimensions. A speculative explanation of an actual allocation decision is not an invented scenario. #288 A00011/A00009 and cues 49–58: speculation recorded as hypothetical vs opinion. Use a consistent policy; unresolved confidence stays unresolved. #288 cues 176–186: competing views reported in speech are not the host's own recommendations.
3. Numeric ownership: #288 cues 187/189 contain 401K designation, not a financial quantity; preserve literal as identifier, require explicit typed disposition, neither pretend it is a quantity nor silently omit it. Cue 286 and 288–289: birth-year threshold and receipt age are distinct from duration. #270 dividend payment month versus consumption installments; #271 deductible contribution base versus actual tax amount. Each token occurrence must be reviewed in relation to its predicate, not assigned a role globally by cue or suffix.
4. Scope: #288 cues 237–240 distinguish premise (return +1%) from estimated consequence (depletion delayed six years); keep conditionality even when reporting an estimate. Cues 3–5 and 571–574 are repeated preview/full explanation; do not require both repetitions for an identical premise. A missing premise is not a harmless coordinate difference. #271 conditions on account/withdrawal source cannot be attached indiscriminately.
5. Time: distinguish recording date, target date, observation date, forecast date, legal effective date, and calculation period. #288 cues 216–218 contain projected future years; topic year 2025 is not their forecast target. Do not silently inherit a topic year for unrelated statements or normalize null as equal.
6. Evaluation: strict scores remain frozen. Diagnostic semantic adjudication may label representation-only, real semantic difference, reference defect, both defective, or unresolved, with source proof. No scoring credit until a prospectively registered validated comparator is used. Do not equate raw condition coordinates or matching literal numbers with semantic equivalence. No blanket equivalence for unknown speaker, missing time, missing qualifiers or units.

## Prospective redesign contract (implementation pending)

Before #277 source reading, freeze a single authoring protocol, schema, code, fixtures, evaluator and source-only grid; same procedure on both turns, no shared semantic answers. Use a single common authoring interface rather than per-video Python scripts that independently map labels. It must require explicit source-based judgments and cannot generate semantic labels from cue IDs, regex or previous turn data. In each of two distinct user turns:
- Pass A: source-only utterance ledger: contiguous cue/character spans, explicit discourse role/unknown, direct vs reported, literal number/identifier/ambiguous fragment and coverage disposition; no claim label or financial truth inferred from lexer.
- Pass B: minimal independently assessable predicate anchored to its nucleus, separate supporting context, exact subject/action/object/polarity; explicit question vs assertion vs recommendation, actual vs hypothetical scenario, epistemic certainty/attribution, condition premise -> consequence, exception, numeric role/value/unit/owner, time type and anchor. No silent default for risk-sensitive unknowns; use OPEN. Every source character and numeric occurrence accounted for, including nonclaims and repeated context. Preserve the original bytes and unresolved ASR.
- Pass C: common deterministic compiler and preflight; reject contradictory labels, lost condition/exception links, clipped tokens, unsupported numeric ownership, unsupported date inheritance, unreviewed identifier tokens and missing evidence. Mechanical checks cannot certify semantic truth.
- Pass D: first/second packet frozen separately; second uses only source and protocol before first body read. Same-turn self-check permitted, no more than two actual user turns for the trial. Capture observed elapsed time and actual work scope; no host authentication/independent model claims.
- Comparison: preserve existing 95/98/0 criteria and 9-axis strict diagnostic. Add non-scoring diagnostic decomposition for source role vs act vs modality, explicit condition relation and numeric/temporal ownership. If schema or comparator changes, version and preregister prospectively; never re-score old failed trials as PASS. Compare exact pairs only by evidence-backed decisions, not overlap; split/merge only diagnostic until equivalence separately proven. Any unresolved high-risk content prevents release.
- Financial truth: current official source/effective-date/applicability review separate E4; unresolved provenance and financial claims remain ineligible for publication. No personalized advice.
- Trial stop: if #277 fails, record result without per-atom repair loop. Identify which general mechanism failed before another engine revision; do not recycle #277 as holdout. Keep #277 unread until code+tests+CI and fixed protocol are verified.

## Implementation gate before next source

G1 shared semantic authoring schema/decision table, with independently represented speech act, epistemic certainty, scenario, time roles and numeric identifier disposition. G2 shared compiler preflight with direct/condition/consequence ownership and numeric occurrence census; old packet replay preserved. G3 actual development excerpts for all six root causes (both valid and invalid cases), synthetic adverse cases, no fixture-specific rules. G4 fresh replay of previous frozen scores with old evaluator unchanged, new diagnostic only, new CI success. G5 register #277 before reading meaning. All G1–G4 must be evidenced before G5. If design or runtime cannot fulfill a gate, report HOLD and stop, not relax.

Status: root-cause census and source spot-check completed. Protocol design documented. G1–G4 implementation and validation remain open. No engine edits in this audit, no new source read, no financial approval, no proof of improved accuracy or independent certification.
