# V200 — E1–E5 integrated readiness test (source-pinned, fail-closed)

**2026-11-20 KST — Development validation, not a financial-knowledge approval.** Derived from V199 head `cef91f97882b328f03873ad654a593dc4cfc707e`. Preserve all owner source, prior E3 judgments, quarantine records, and the public `main` branch.

## Why this is an engine issue, not another CMA fact-checking pass

1. V176's `compile_native_v6_stage()` creates a native V6 structural preview, but assigns unresolved stance and unknown speaker on every candidate. The native staging object explicitly says `v123_invoked=False`, `e4_invoked=False`, `e5_invoked=False`.
2. V199's six residual decisions and 12 official-web-text comparisons hard-code particular CMA atom IDs. They prevent mistaken authority claims but do not generalize semantic extraction or prove E3 accuracy.
3. The original CMA source and private V199 checkpoint are not embedded in this public branch. Real audio, source-specific issuer terms, independent gold results, and trusted host turn attestation remain unavailable from public code alone.

## Changes in this branch

- `v200_e1_e5_live_gate.py`: generic, video-agnostic live interrogation of the **actual** V176 SQLite audit and frozen native V6 staging. It checks full cue census, source/head consistency, candidate census, source qualifier mapping, stance/speaker completeness, optional pinned V199 object provenance, and the native E4/E5 invocation flags. It **rejects a hand-written dictionary pretending to be a verified engine**.
- `test_v200_e1_e5_live_gate.py`: synthetic adverse and restart tests, including a completed full source review that still must not be reported as an approved financial knowledge item.
- CI runs the existing V176–V199 compatibility tests **and** the new V200 gate tests. Tests prove software invariants, not semantic precision/recall.

## E1–E5 operational decisions

| Stage | Observable capability | V200 verdict | Release requirement |
|---|---|---|---|
| E1 | V176 original-cue census, hash-chained SQLite, restart | **PARTIAL** | One real source-to-approval replay with nonfabricated ChatGPT host interactions |
| E2 | Native staged atoms, condition/exception mapping counts | **HOLD** | General semantic split, parent/condition/exception, stance and speaker validation against independent source reference |
| E3 | Two user commands, owner-private second-review/corrections | **HOLD** | Trustworthy two-turn provenance plus blind frozen gold: precision ≥95%, recall ≥98%, high-risk missed=0 |
| E4 | Frozen V123/native approval authority exists separately | **NOT RUN** | Actual valid-approval acceptance and invalid-approval rejection under frozen gate, not synthetic-only rejections |
| E5 | Atomic knowledge publication is separately gated | **NOT RUN / 0 published** | 13-segment all-approved atomic transaction and rollback/restart test; no partial write |

### Design boundary

`evaluate_live` is **read-only**. It does not replace a real inference model, external evidence, a trustworthy two-user-turn attestation, V123 adjudication, or the E5 transactional writer. It must not be treated as an E3 PASS mechanism. It returns counts and hashes, not private SRT text or verdicts.

### Next implementation bottleneck

The next substantive engine change must be a video-agnostic E2 semantic projection protocol: candidate claims must preserve independently source-anchored condition/exception, speaker, stance and parent identity. Only after independently evaluated real-video E3 review can a pinned native E4 approval be attempted. Never convert the V200 readiness report into a self-authorizing E4/E5 receipt. The 72 remaining V199 CMA financial checks are a downstream evidence backlog, not the first engineering priority.
